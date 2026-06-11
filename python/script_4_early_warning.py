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
# STEP 2 - LOAD MASTER VIEW AND RISK SCORES
# ============================================

print("Loading data...")

master_df = pd.read_sql(
    "SELECT * FROM master_food_security", conn
)

risk_df = pd.read_sql(
    "SELECT * FROM risk_scores", conn
)

print(f"Master rows loaded:     {len(master_df)}")
print(f"Risk score rows loaded: {len(risk_df)}")

# ============================================
# STEP 3 - DEFINE WHAT DETERIORATING MEANS
# ============================================

# A variable is deteriorating if it gets worse
# for 3 or more consecutive years

# Variables where DECLINE = getting worse
declining_bad = [
    "yield_per_hectare",
    "rainfall_mm",
    "gdp_per_capita"
]

# Variables where INCREASE = getting worse
increasing_bad = [
    "import_dependency_percent",
    "conflict_score",
    "cereals_price_index"
]

def count_consecutive_decline(series):
    """
    Counts how many consecutive years
    a series has been declining
    """
    series = series.reset_index(drop=True)
    count = 0
    for i in range(len(series) - 1, 0, -1):
        if series[i] < series[i-1]:
            count += 1
        else:
            break
    return count

def count_consecutive_increase(series):
    """
    Counts how many consecutive years
    a series has been increasing
    """
    series = series.reset_index(drop=True)
    count = 0
    for i in range(len(series) - 1, 0, -1):
        if series[i] > series[i-1]:
            count += 1
        else:
            break
    return count

# ============================================
# STEP 4 - ANALYZE EACH COUNTRY
# ============================================

print("\nAnalyzing deterioration patterns...")

CONSECUTIVE_YEARS = 3  # flag if worsening 3+ years
results = []

countries = master_df["country_name"].unique()

for country in countries:

    country_df = master_df[
        master_df["country_name"] == country
    ].sort_values("year")

    if len(country_df) < CONSECUTIVE_YEARS + 1:
        continue

    # Get latest risk score and level
    risk_row = risk_df[
        risk_df["country_name"] == country
    ].sort_values("year").iloc[-1] if len(
        risk_df[risk_df["country_name"] == country]
    ) > 0 else None

    if risk_row is None:
        continue

    latest_score = float(risk_row["final_score"])
    risk_level   = risk_row["risk_level"]

    # Count how many variables are deteriorating
    variables_declining = []

    for col in declining_bad:
        if col in country_df.columns:
            consecutive = count_consecutive_decline(
                country_df[col]
            )
            if consecutive >= CONSECUTIVE_YEARS:
                variables_declining.append(
                    f"{col} declining {consecutive}yrs"
                )

    for col in increasing_bad:
        if col in country_df.columns:
            consecutive = count_consecutive_increase(
                country_df[col]
            )
            if consecutive >= CONSECUTIVE_YEARS:
                variables_declining.append(
                    f"{col} rising {consecutive}yrs"
                )

    num_deteriorating = len(variables_declining)

    # Calculate deterioration severity
    if num_deteriorating >= 5:
        severity = "CRITICAL"
    elif num_deteriorating >= 4:
        severity = "HIGH"
    elif num_deteriorating >= 3:
        severity = "MODERATE"
    elif num_deteriorating >= 2:
        severity = "WATCH"
    else:
        severity = "STABLE"

    # Calculate score change over last 3 years
    recent = country_df.tail(4)
    if len(recent) >= 2:
        score_recent = risk_df[
            risk_df["country_name"] == country
        ].sort_values("year").tail(4)

        if len(score_recent) >= 2:
            score_change = float(
                score_recent["final_score"].iloc[-1] -
                score_recent["final_score"].iloc[0]
            )
        else:
            score_change = 0
    else:
        score_change = 0

    results.append({
        "country_name"        : country,
        "current_score"       : round(latest_score, 2),
        "risk_level"          : risk_level,
        "variables_worsening" : num_deteriorating,
        "severity"            : severity,
        "score_change_3yr"    : round(score_change, 2),
        "deteriorating_vars"  : " | ".join(variables_declining)
        if variables_declining else "None"
    })

warning_df = pd.DataFrame(results)

# ============================================
# STEP 5 - FILTER TO MEANINGFUL FLAGS
# ============================================

# Most interesting = currently Green or Orange
# but multiple variables declining
# These are the hidden risks

# Load GDP to filter out wealthy countries
gdp_avg = pd.read_sql("""
    SELECT country_name,
           AVG(gdp_per_capita) AS avg_gdp
    FROM gdp
    GROUP BY country_name
""", conn)

gdp_threshold = gdp_avg["avg_gdp"].quantile(0.75)

warning_df = warning_df.merge(
    gdp_avg, on="country_name", how="left"
)

watch_list = warning_df[
    (warning_df["variables_worsening"] >= 2) &
    (warning_df["risk_level"].isin(["Green", "Orange"])) &
    (warning_df["avg_gdp"] < gdp_threshold)
].sort_values(
    ["variables_worsening", "score_change_3yr"],
    ascending=[False, False]
)

# Already red but accelerating
accelerating = warning_df[
    (warning_df["risk_level"] == "Red") &
    (warning_df["score_change_3yr"] > 5)
].sort_values("score_change_3yr", ascending=False)

# ============================================
# STEP 6 - PRINT RESULTS
# ============================================

print("\n--- HIDDEN RISK WATCH LIST ---")
print("Currently Green/Orange but deteriorating fast")
print(watch_list[[
    "country_name", "current_score",
    "risk_level", "variables_worsening",
    "severity", "score_change_3yr"
]].head(25).to_string(index=False))

print("\n--- CRITICAL HIDDEN RISKS ---")
critical = watch_list[
    watch_list["severity"].isin(["CRITICAL", "HIGH"])
]
if len(critical) > 0:
    print(critical[[
        "country_name", "current_score",
        "variables_worsening",
        "deteriorating_vars"
    ]].to_string(index=False))
else:
    print("None found")

print("\n--- ALREADY RED BUT ACCELERATING ---")
print(accelerating[[
    "country_name", "current_score",
    "score_change_3yr", "variables_worsening"
]].head(15).to_string(index=False))

print("\n--- SUMMARY ---")
print(f"Total countries analyzed:        {len(warning_df)}")
print(f"Hidden risks (Green/Orange):     {len(watch_list)}")
print(f"Critical hidden risks:           "
      f"{len(watch_list[watch_list['severity'].isin(['CRITICAL','HIGH'])])}")
print(f"Red countries accelerating:      {len(accelerating)}")

# ============================================
# STEP 7 - PUSH TO SQL
# ============================================

print("\nPushing early warning data to PostgreSQL...")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS early_warning (
        id                   SERIAL PRIMARY KEY,
        country_name         VARCHAR(100),
        current_score        FLOAT,
        risk_level           VARCHAR(20),
        variables_worsening  INT,
        severity             VARCHAR(20),
        score_change_3yr     FLOAT,
        deteriorating_vars   TEXT
    );
""")

cursor.execute("DELETE FROM early_warning;")

for _, row in warning_df.iterrows():
    cursor.execute("""
        INSERT INTO early_warning
            (country_name, current_score, risk_level,
             variables_worsening, severity,
             score_change_3yr, deteriorating_vars)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        row["country_name"],
        row["current_score"],
        row["risk_level"],
        int(row["variables_worsening"]),
        row["severity"],
        float(row["score_change_3yr"]),
        row["deteriorating_vars"]
    ))

conn.commit()
print(f"Early warning data pushed: {len(warning_df)} countries")

cursor.close()
conn.close()
print("\nScript 4 complete. Early warning system done.")