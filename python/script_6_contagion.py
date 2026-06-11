import pandas as pd
import numpy as np
import psycopg2
from config import DB_CONFIG

conn = psycopg2.connect(
    host=DB_CONFIG["host"],
    port=DB_CONFIG["port"],
    database=DB_CONFIG["database"],
    user=DB_CONFIG["user"],
    password=DB_CONFIG["password"]
)
print("Connected successfully")

# ============================================
# STEP 1 - LOAD ALL COUNTRIES FROM DATABASE
# ============================================

print("Loading data...")

risk_df = pd.read_sql(
    "SELECT * FROM risk_scores WHERE year = 2022",
    conn
)

import_df = pd.read_sql(
    "SELECT * FROM import_dependency WHERE year = 2022",
    conn
)

gdp_df = pd.read_sql("""
    SELECT country_name, AVG(gdp_per_capita) AS avg_gdp
    FROM gdp
    GROUP BY country_name
""", conn)

print(f"Countries in risk scores: {len(risk_df)}")

# ============================================
# STEP 2 - ASSIGN REGIONS AUTOMATICALLY
# Using a complete country to region mapping
# ============================================

country_region_map = {
    # East Africa
    "Kenya"              : "East Africa",
    "Ethiopia"           : "East Africa",
    "Uganda"             : "East Africa",
    "Tanzania"           : "East Africa",
    "Rwanda"             : "East Africa",
    "Burundi"            : "East Africa",
    "South Sudan"        : "East Africa",
    "Sudan"              : "East Africa",
    "Eritrea"            : "East Africa",
    "Djibouti"           : "East Africa",
    "Somalia"            : "East Africa",
    "Comoros"            : "East Africa",
    "Seychelles"         : "East Africa",

    # West Africa
    "Nigeria"            : "West Africa",
    "Ghana"              : "West Africa",
    "Senegal"            : "West Africa",
    "Mali"               : "West Africa",
    "Burkina Faso"       : "West Africa",
    "Niger"              : "West Africa",
    "Chad"               : "West Africa",
    "Cameroon"           : "West Africa",
    "Benin"              : "West Africa",
    "Togo"               : "West Africa",
    "Guinea"             : "West Africa",
    "Sierra Leone"       : "West Africa",
    "Liberia"            : "West Africa",
    "Gambia"             : "West Africa",
    "Guinea-Bissau"      : "West Africa",
    "Mauritania"         : "West Africa",
    "Cabo Verde"         : "West Africa",
    "Cote d'Ivoire"      : "West Africa",

    # Central Africa
    "Democratic Republic of the Congo" : "Central Africa",
    "Central African Republic"         : "Central Africa",
    "Republic of Congo"                : "Central Africa",
    "Gabon"                            : "Central Africa",
    "Equatorial Guinea"                : "Central Africa",
    "Sao Tome and Principe"            : "Central Africa",

    # North Africa
    "Egypt"              : "North Africa",
    "Libya"              : "North Africa",
    "Tunisia"            : "North Africa",
    "Algeria"            : "North Africa",
    "Morocco"            : "North Africa",

    # Southern Africa
    "South Africa"       : "Southern Africa",
    "Zimbabwe"           : "Southern Africa",
    "Zambia"             : "Southern Africa",
    "Mozambique"         : "Southern Africa",
    "Malawi"             : "Southern Africa",
    "Angola"             : "Southern Africa",
    "Namibia"            : "Southern Africa",
    "Botswana"           : "Southern Africa",
    "Lesotho"            : "Southern Africa",
    "Eswatini"           : "Southern Africa",
    "Madagascar"         : "Southern Africa",

    # Middle East
    "Yemen"                    : "Middle East",
    "Jordan"                   : "Middle East",
    "Lebanon"                  : "Middle East",
    "Syria"                    : "Middle East",
    "Iraq"                     : "Middle East",
    "Iran, Islamic Republic of": "Middle East",
    "Saudi Arabia"             : "Middle East",
    "United Arab Emirates"     : "Middle East",
    "Kuwait"                   : "Middle East",
    "Qatar"                    : "Middle East",
    "Bahrain"                  : "Middle East",
    "Oman"                     : "Middle East",
    "Israel"                   : "Middle East",
    "Palestine"                : "Middle East",

    # South Asia
    "India"              : "South Asia",
    "Pakistan"           : "South Asia",
    "Bangladesh"         : "South Asia",
    "Nepal"              : "South Asia",
    "Afghanistan"        : "South Asia",
    "Sri Lanka"          : "South Asia",
    "Maldives"           : "South Asia",
    "Bhutan"             : "South Asia",

    # Southeast Asia
    "Indonesia"                        : "Southeast Asia",
    "Philippines"                      : "Southeast Asia",
    "Viet Nam"                         : "Southeast Asia",
    "Myanmar"                          : "Southeast Asia",
    "Thailand"                         : "Southeast Asia",
    "Malaysia"                         : "Southeast Asia",
    "Cambodia"                         : "Southeast Asia",
    "Lao People's Democratic Republic" : "Southeast Asia",
    "Timor-Leste"                      : "Southeast Asia",
    "Singapore"                        : "Southeast Asia",
    "Brunei Darussalam"                : "Southeast Asia",

    # East Asia
    "China"              : "East Asia",
    "Japan"              : "East Asia",
    "South Korea"        : "East Asia",
    "Mongolia"           : "East Asia",
    "Taiwan"             : "East Asia",

    # Central Asia
    "Kazakhstan"         : "Central Asia",
    "Uzbekistan"         : "Central Asia",
    "Turkmenistan"       : "Central Asia",
    "Tajikistan"         : "Central Asia",
    "Kyrgyzstan"         : "Central Asia",

    # Eastern Europe
    "Ukraine"                    : "Eastern Europe",
    "Moldova, Republic of"       : "Eastern Europe",
    "Belarus"                    : "Eastern Europe",
    "Romania"                    : "Eastern Europe",
    "Bulgaria"                   : "Eastern Europe",
    "Serbia"                     : "Eastern Europe",
    "Albania"                    : "Eastern Europe",
    "North Macedonia"            : "Eastern Europe",
    "Bosnia and Herzegovina"     : "Eastern Europe",
    "Montenegro"                 : "Eastern Europe",
    "Georgia"                    : "Eastern Europe",
    "Armenia"                    : "Eastern Europe",
    "Azerbaijan"                 : "Eastern Europe",
    "Kosovo"                     : "Eastern Europe",
    "Hungary"                    : "Eastern Europe",
    "Poland"                     : "Eastern Europe",
    "Czechia"                    : "Eastern Europe",
    "Slovakia"                   : "Eastern Europe",
    "Slovenia"                   : "Eastern Europe",
    "Croatia"                    : "Eastern Europe",
    "Lithuania"                  : "Eastern Europe",
    "Latvia"                     : "Eastern Europe",
    "Estonia"                    : "Eastern Europe",

    # Western Europe
    "Germany"            : "Western Europe",
    "France"             : "Western Europe",
    "Spain"              : "Western Europe",
    "Italy"              : "Western Europe",
    "Portugal"           : "Western Europe",
    "Greece"             : "Western Europe",
    "Switzerland"        : "Western Europe",
    "Austria"            : "Western Europe",
    "Belgium"            : "Western Europe",
    "Netherlands"        : "Western Europe",
    "Ireland"            : "Western Europe",
    "Norway"             : "Western Europe",
    "Denmark"            : "Western Europe",
    "Finland"            : "Western Europe",
    "Sweden"             : "Western Europe",
    "Iceland"            : "Western Europe",
    "Luxembourg"         : "Western Europe",
    "Malta"              : "Western Europe",
    "Cyprus"             : "Western Europe",

    # North America
    "United States"      : "North America",
    "Canada"             : "North America",
    "Mexico"             : "North America",

    # Central America Caribbean
    "Haiti"                    : "Central America Caribbean",
    "Cuba"                     : "Central America Caribbean",
    "Dominican Republic"       : "Central America Caribbean",
    "Guatemala"                : "Central America Caribbean",
    "Honduras"                 : "Central America Caribbean",
    "El Salvador"              : "Central America Caribbean",
    "Nicaragua"                : "Central America Caribbean",
    "Costa Rica"               : "Central America Caribbean",
    "Panama"                   : "Central America Caribbean",
    "Jamaica"                  : "Central America Caribbean",
    "Trinidad and Tobago"      : "Central America Caribbean",
    "Barbados"                 : "Central America Caribbean",
    "Belize"                   : "Central America Caribbean",
    "Guyana"                   : "Central America Caribbean",
    "Suriname"                 : "Central America Caribbean",

    # South America
    "Brazil"                                   : "South America",
    "Colombia"                                 : "South America",
    "Venezuela, Bolivarian Republic of"        : "South America",
    "Peru"                                     : "South America",
    "Ecuador"                                  : "South America",
    "Bolivia"                                  : "South America",
    "Paraguay"                                 : "South America",
    "Argentina"                                : "South America",
    "Chile"                                    : "South America",

    # Pacific Islands
    "Papua New Guinea"                     : "Pacific Islands",
    "Solomon Islands"                      : "Pacific Islands",
    "Fiji"                                 : "Pacific Islands",
    "Vanuatu"                              : "Pacific Islands",
    "Samoa"                                : "Pacific Islands",
    "Tonga"                                : "Pacific Islands",
    "Kiribati"                             : "Pacific Islands",
    "Marshall Islands"                     : "Pacific Islands",
    "Micronesia, Federated States of"      : "Pacific Islands",
    "Palau"                                : "Pacific Islands",
    "Tuvalu"                               : "Pacific Islands",
    "Nauru"                                : "Pacific Islands",
    "New Caledonia"                        : "Pacific Islands",
    "French Polynesia"                     : "Pacific Islands",
}

# Regional food producers
# Countries whose collapse affects the whole region
regional_producers = {
    "East Africa"              : ["Ethiopia", "Tanzania", "Uganda"],
    "West Africa"              : ["Nigeria", "Ghana", "Senegal"],
    "Central Africa"           : ["Democratic Republic of the Congo", "Cameroon"],
    "North Africa"             : ["Egypt", "Morocco", "Algeria"],
    "Southern Africa"          : ["South Africa", "Zimbabwe", "Zambia"],
    "Middle East"              : ["Turkey", "Iran, Islamic Republic of"],
    "South Asia"               : ["India", "Pakistan"],
    "Southeast Asia"           : ["Viet Nam", "Thailand", "Indonesia"],
    "East Asia"                : ["China", "Japan"],
    "Central Asia"             : ["Kazakhstan", "Uzbekistan"],
    "Eastern Europe"           : ["Ukraine", "Romania", "Poland"],
    "Western Europe"           : ["France", "Germany", "Spain"],
    "North America"            : ["United States", "Canada"],
    "Central America Caribbean": ["Guatemala", "Dominican Republic"],
    "South America"            : ["Brazil", "Argentina"],
    "Pacific Islands"          : ["Papua New Guinea", "Fiji"],
}

# ============================================
# STEP 3 - ASSIGN REGION TO EVERY COUNTRY
# IN THE DATABASE AUTOMATICALLY
# ============================================

# Add region column to risk_df
risk_df["region"] = risk_df["country_name"].map(
    country_region_map
)

# For any country not in our map assign Unknown
risk_df["region"] = risk_df["region"].fillna("Other")

print(f"\nRegion assignment:")
print(risk_df["region"].value_counts())

unmatched = risk_df[risk_df["region"] == "Other"][
    "country_name"
].tolist()
if unmatched:
    print(f"\nCountries not assigned to region: {unmatched}")

# ============================================
# STEP 4 - IDENTIFY CRISIS PRODUCERS
# ============================================

print("\nIdentifying crisis producers...")

crisis_producers = []

for region, producers in regional_producers.items():
    for producer in producers:
        producer_risk = risk_df[
            risk_df["country_name"] == producer
        ]
        if len(producer_risk) > 0:
            score = float(
                producer_risk["final_score"].iloc[0]
            )
            level = producer_risk["risk_level"].iloc[0]
            if score >= 50:
                crisis_producers.append({
                    "region"        : region,
                    "producer"      : producer,
                    "producer_score": round(score, 2),
                    "risk_level"    : level
                })
                print(f"  {region}: {producer} "
                      f"score {score:.1f} {level}")

crisis_df = pd.DataFrame(crisis_producers)

# ============================================
# STEP 5 - CALCULATE CONTAGION FOR EVERY
# COUNTRY IN DATABASE
# ============================================

print("\nCalculating contagion risk for all countries...")

results = []

for _, country_row in risk_df.iterrows():

    country    = country_row["country_name"]
    region     = country_row["region"]
    own_score  = float(country_row["final_score"])
    risk_level = country_row["risk_level"]

    # Get region crisis producers
    region_crisis = crisis_df[
        crisis_df["region"] == region
    ] if len(crisis_df) > 0 else pd.DataFrame()

    if len(region_crisis) > 0:
        avg_producer_crisis = float(
            region_crisis["producer_score"].mean()
        )
        num_crisis_producers = len(region_crisis)
        worst_producer = region_crisis.loc[
            region_crisis["producer_score"].idxmax(),
            "producer"
        ]
    else:
        avg_producer_crisis = 0
        num_crisis_producers = 0
        worst_producer = "None"

    # Get import dependency
    import_row = import_df[
        import_df["country_name"] == country
    ]
    import_pct = float(
        import_row["import_dependency_percent"].iloc[0]
    ) if len(import_row) > 0 else 50.0

    # Get GDP
    gdp_row = gdp_df[gdp_df["country_name"] == country]
    avg_gdp = float(
        gdp_row["avg_gdp"].iloc[0]
    ) if len(gdp_row) > 0 else 5000.0

    # Already in crisis
    if own_score >= 61:
        contagion_score = 0
        contagion_level = "Already in crisis"

    else:
        # Base contagion score
        contagion_score = (
            avg_producer_crisis * 0.5 +
            import_pct          * 0.3 +
            own_score           * 0.2
        ) / 100 * 100

        # GDP dampening — wealthy countries
        # can absorb regional shocks better
        gdp_dampener = max(0.4, 1 - (avg_gdp / 100000))
        contagion_score = contagion_score * gdp_dampener

        contagion_score = min(
            round(contagion_score, 2), 100
        )

        if contagion_score >= 70:
            contagion_level = "CRITICAL contagion risk"
        elif contagion_score >= 55:
            contagion_level = "HIGH contagion risk"
        elif contagion_score >= 40:
            contagion_level = "MODERATE contagion risk"
        else:
            contagion_level = "LOW contagion risk"

    results.append({
        "country_name"        : country,
        "region"              : region,
        "own_score"           : round(own_score, 2),
        "own_risk_level"      : risk_level,
        "import_dependency"   : round(import_pct, 2),
        "num_crisis_producers": num_crisis_producers,
        "worst_producer"      : worst_producer,
        "avg_producer_crisis" : round(avg_producer_crisis, 2),
        "contagion_score"     : contagion_score,
        "contagion_level"     : contagion_level
    })

contagion_df = pd.DataFrame(results)

# ============================================
# STEP 6 - PRINT RESULTS
# ============================================

print("\n--- CRITICAL CONTAGION RISK ---")
critical = contagion_df[
    contagion_df["contagion_level"] == "CRITICAL contagion risk"
].sort_values("contagion_score", ascending=False)
print(critical[[
    "country_name", "region", "own_score",
    "import_dependency", "contagion_score",
    "worst_producer"
]].to_string(index=False) if len(critical) > 0 else "None")

print("\n--- HIGH CONTAGION RISK ---")
high = contagion_df[
    contagion_df["contagion_level"] == "HIGH contagion risk"
].sort_values("contagion_score", ascending=False)
print(high[[
    "country_name", "region", "own_score",
    "import_dependency", "contagion_score",
    "worst_producer"
]].head(20).to_string(index=False) if len(high) > 0 else "None")

print("\n--- REGIONAL SUMMARY ---")
regional_summary = contagion_df.groupby("region").agg(
    total_countries   = ("country_name", "count"),
    avg_contagion     = ("contagion_score", "mean"),
    critical_count    = ("contagion_level",
                         lambda x: (x == "CRITICAL contagion risk").sum()),
    high_count        = ("contagion_level",
                         lambda x: (x == "HIGH contagion risk").sum())
).round(2).sort_values("avg_contagion", ascending=False)

print(regional_summary.to_string())

print(f"\nTotal countries processed: {len(contagion_df)}")
print(f"Critical risk:  {len(critical)}")
print(f"High risk:      {len(high)}")

# ============================================
# STEP 7 - PUSH TO SQL
# ============================================

print("\nPushing to PostgreSQL...")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS contagion;")
cursor.execute("""
    CREATE TABLE contagion (
        id                    SERIAL PRIMARY KEY,
        country_name          VARCHAR(100),
        region                VARCHAR(100),
        own_score             FLOAT,
        own_risk_level        VARCHAR(20),
        import_dependency     FLOAT,
        num_crisis_producers  INT,
        worst_producer        VARCHAR(100),
        avg_producer_crisis   FLOAT,
        contagion_score       FLOAT,
        contagion_level       VARCHAR(50)
    );
""")

for _, row in contagion_df.iterrows():
    cursor.execute("""
        INSERT INTO contagion
            (country_name, region, own_score,
             own_risk_level, import_dependency,
             num_crisis_producers, worst_producer,
             avg_producer_crisis, contagion_score,
             contagion_level)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        row["country_name"],
        row["region"],
        float(row["own_score"]),
        row["own_risk_level"],
        float(row["import_dependency"]),
        int(row["num_crisis_producers"]),
        row["worst_producer"],
        float(row["avg_producer_crisis"]),
        float(row["contagion_score"]),
        row["contagion_level"]
    ))

conn.commit()
print(f"Contagion data pushed: {len(contagion_df)} rows")

cursor.close()
conn.close()
print("\nScript 6 complete.")