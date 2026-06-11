import pandas as pd
import numpy as np
import psycopg2
from config import DB_CONFIG

# ============================================
# STEP 1 - CONNECT
# ============================================

conn = psycopg2.connect(
    host=DB_CONFIG["host"],
    port=DB_CONFIG["port"],
    database=DB_CONFIG["database"],
    user=DB_CONFIG["user"],
    password=DB_CONFIG["password"]
)
print("Connected successfully")

# ============================================
# STEP 2 - LOAD RISK SCORES AND POPULATION
# ============================================

print("Loading data...")

risk_df = pd.read_sql(
    "SELECT * FROM risk_scores", conn
)

# Load population from World Bank GDP table
# World Bank GDP file includes population
pop_df = pd.read_sql("""
    SELECT country_name,
           year,
           gdp_per_capita
    FROM gdp
    WHERE year = 2022
""", conn)

print(f"Risk scores loaded:  {len(risk_df)}")

# ============================================
# STEP 3 - LOAD POPULATION FROM COUNTRIES TABLE
# If you have population in countries table
# ============================================

# Check if countries table has population
try:
    countries_df = pd.read_sql("""
        SELECT country_name, population
        FROM countries
        WHERE population IS NOT NULL
    """, conn)
    print(f"Population data loaded: {len(countries_df)} countries")
    has_population = len(countries_df) > 0
except:
    conn.rollback()
    has_population = False
    print("No population table found — using estimates")

# ============================================
# STEP 4 - IF NO POPULATION TABLE
# Use World Bank population estimates
# ============================================

if not has_population:
    # Approximate population data for key countries
    # These are 2022 estimates in millions
    population_data = {
        "China"                  : 1412,
        "India"                  : 1407,
        "United States"          : 333,
        "Indonesia"              : 275,
        "Pakistan"               : 231,
        "Brazil"                 : 215,
        "Nigeria"                : 218,
        "Bangladesh"             : 170,
        "Ethiopia"               : 123,
        "Mexico"                 : 130,
        "Russia"                 : 144,
        "Philippines"            : 115,
        "Egypt"                  : 104,
        "Democratic Republic of the Congo" : 100,
        "Viet Nam"               : 98,
        "Iran, Islamic Republic of" : 87,
        "Turkey"                 : 85,
        "Germany"                : 84,
        "Thailand"               : 72,
        "United Kingdom"         : 67,
        "France"                 : 68,
        "Tanzania"               : 63,
        "South Africa"           : 60,
        "Myanmar"                : 54,
        "Kenya"                  : 55,
        "Colombia"               : 51,
        "Spain"                  : 47,
        "Uganda"                 : 48,
        "Argentina"              : 46,
        "Algeria"                : 45,
        "Sudan"                  : 45,
        "Iraq"                   : 42,
        "Ukraine"                : 41,
        "Afghanistan"            : 41,
        "Poland"                 : 38,
        "Canada"                 : 38,
        "Morocco"                : 37,
        "Saudi Arabia"           : 36,
        "Uzbekistan"             : 35,
        "Peru"                   : 33,
        "Malaysia"               : 33,
        "Angola"                 : 35,
        "Mozambique"             : 33,
        "Ghana"                  : 33,
        "Yemen"                  : 34,
        "Nepal"                  : 30,
        "Venezuela, Bolivarian Republic of" : 29,
        "Madagascar"             : 28,
        "Cameroon"               : 28,
        "Ivory Coast"            : 27,
        "Niger"                  : 25,
        "Mali"                   : 22,
        "Burkina Faso"           : 22,
        "Malawi"                 : 20,
        "Syria"                  : 21,
        "Chad"                   : 18,
        "Somalia"                : 17,
        "South Sudan"            : 11,
        "Haiti"                  : 11,
        "Zimbabwe"               : 16,
        "Rwanda"                 : 14,
        "Benin"                  : 13,
        "Burundi"                : 13,
        "Bolivia"                : 12,
        "Tunisia"                : 12,
        "Jordan"                 : 10,
        "Libya"                  : 7,
        "Lebanon"                : 5,
        "Sierra Leone"           : 8,
        "Liberia"                : 5,
        "Central African Republic" : 5,
        "Eritrea"                : 3,
        "Gambia"                 : 2,
        "Lesotho"                : 2,
        "Mauritania"             : 4,
        "Djibouti"               : 1,
    }

    countries_df = pd.DataFrame([
        {"country_name": k, "population": v * 1_000_000}
        for k, v in population_data.items()
    ])
    print(f"Using built-in population estimates: "
          f"{len(countries_df)} countries")

# ============================================
# STEP 5 - MERGE AND CALCULATE EXPOSURE
# ============================================

print("\nCalculating population exposure...")

# Get latest year risk scores only
latest_risk = risk_df[
    risk_df["year"] == risk_df["year"].max()
].copy()

# Merge with population
exposure_df = latest_risk.merge(
    countries_df, on="country_name", how="left"
)

# Calculate people at risk
exposure_df["people_at_risk"] = (
    exposure_df["population"] *
    (exposure_df["final_score"] / 100)
).round(0)

# Classify exposure level
def exposure_level(score):
    if score >= 61:
        return "High Risk"
    elif score >= 31:
        return "Moderate Risk"
    else:
        return "Low Risk"

exposure_df["exposure_level"] = exposure_df[
    "final_score"
].apply(exposure_level)

# ============================================
# STEP 6 - PRINT RESULTS
# ============================================

print("\n--- TOP 20 COUNTRIES BY PEOPLE AT RISK ---")
top_exposure = exposure_df.dropna(
    subset=["people_at_risk"]
).nlargest(20, "people_at_risk")

top_exposure["population_M"]    = (
    top_exposure["population"] / 1_000_000
).round(1)
top_exposure["people_at_risk_M"] = (
    top_exposure["people_at_risk"] / 1_000_000
).round(1)

print(top_exposure[[
    "country_name", "final_score",
    "risk_level", "population_M",
    "people_at_risk_M"
]].to_string(index=False))

print("\n--- GLOBAL EXPOSURE SUMMARY ---")
high_risk = exposure_df[
    exposure_df["exposure_level"] == "High Risk"
]
moderate_risk = exposure_df[
    exposure_df["exposure_level"] == "Moderate Risk"
]
low_risk = exposure_df[
    exposure_df["exposure_level"] == "Low Risk"
]

high_pop = high_risk["population"].sum() / 1_000_000_000
mod_pop  = moderate_risk["population"].sum() / 1_000_000_000
low_pop  = low_risk["population"].sum() / 1_000_000_000

high_exposed = high_risk["people_at_risk"].sum() / 1_000_000_000
mod_exposed  = moderate_risk["people_at_risk"].sum() / 1_000_000_000

print(f"\nHigh Risk countries:")
print(f"  Countries:        {len(high_risk)}")
print(f"  Total population: {high_pop:.2f} billion")
print(f"  People at risk:   {high_exposed:.2f} billion")

print(f"\nModerate Risk countries:")
print(f"  Countries:        {len(moderate_risk)}")
print(f"  Total population: {mod_pop:.2f} billion")
print(f"  People at risk:   {mod_exposed:.2f} billion")

print(f"\nTotal people exposed globally: "
      f"{(high_exposed + mod_exposed):.2f} billion")

print("\n--- HIGHEST IMPACT SINGLE COUNTRIES ---")
print("Countries where most people are affected:")
print(top_exposure[[
    "country_name", "risk_level",
    "people_at_risk_M"
]].head(10).to_string(index=False))

# ============================================
# STEP 7 - PUSH TO SQL
# ============================================

print("\nPushing population exposure to PostgreSQL...")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS population_exposure (
        id               SERIAL PRIMARY KEY,
        country_name     VARCHAR(100),
        year             INT,
        final_score      FLOAT,
        risk_level       VARCHAR(20),
        population       BIGINT,
        people_at_risk   BIGINT,
        exposure_level   VARCHAR(20)
    );
""")

cursor.execute("DELETE FROM population_exposure;")

for _, row in exposure_df.iterrows():
    cursor.execute("""
        INSERT INTO population_exposure
            (country_name, year, final_score,
             risk_level, population,
             people_at_risk, exposure_level)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        row["country_name"],
        int(row["year"]),
        float(row["final_score"]),
        row["risk_level"],
        None if pd.isna(row["population"])
             else int(row["population"]),
        None if pd.isna(row["people_at_risk"])
             else int(row["people_at_risk"]),
        row["exposure_level"]
    ))

conn.commit()
print(f"Population exposure pushed: {len(exposure_df)} rows")

cursor.close()
conn.close()
print("\nScript 5 complete. Population exposure done.")