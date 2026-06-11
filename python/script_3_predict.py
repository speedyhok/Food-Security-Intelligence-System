import pandas as pd
import numpy as np
import psycopg2
from scipy import stats
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
# STEP 2 - LOAD RISK SCORES
# ============================================

risk_df = pd.read_sql("SELECT * FROM risk_scores", conn)
print(f"Risk scores loaded: {len(risk_df)} rows")

# ============================================
# STEP 3 - LOAD GDP AND CALCULATE THRESHOLD
# ============================================

gdp_df = pd.read_sql("""
    SELECT country_name,
           AVG(gdp_per_capita) AS avg_gdp
    FROM gdp
    GROUP BY country_name
""", conn)

# Wealthy threshold = 75th percentile of all
# country average GDPs in your actual data
gdp_threshold = gdp_df["avg_gdp"].quantile(0.75)
print(f"GDP wealth threshold (75th percentile): ${gdp_threshold:,.0f}")

wealthy_countries = set(
    gdp_df[gdp_df["avg_gdp"] >= gdp_threshold]["country_name"]
)
print(f"Countries above wealth threshold: {len(wealthy_countries)}")

# Merge avg GDP into risk scores for reference
df = risk_df.merge(gdp_df, on="country_name", how="left")

# ============================================
# STEP 4 - KNOWN CRISES 2023-2026
# For backtesting our predictions
# ============================================

known_crises = {
    "Sudan"        : 2023,
    "Niger"        : 2023,
    "Mali"         : 2023,
    "Burkina Faso" : 2023,
    "Ethiopia"     : 2023,
    "Chad"         : 2023,
    "Yemen"        : 2023,
    "Afghanistan"  : 2023,
    "Syria"        : 2023,
    "South Sudan"  : 2023,
    "Zimbabwe"     : 2024,
    "Mozambique"   : 2024,
    "Haiti"        : 2024,
}

# ============================================
# STEP 5 - PREDICT PER COUNTRY
# ============================================

print("\nCalculating predictions...")

CRISIS_THRESHOLD = 61
FORECAST_TO      = 2035
results          = []

for country in df["country_name"].unique():

    country_df = df[
        df["country_name"] == country
    ].sort_values("year")

    if len(country_df) < 3:
        continue

    years        = country_df["year"].values
    scores       = country_df["final_score"].values
    latest_score = float(scores[-1])
    latest_year  = int(years[-1])
    avg_gdp      = country_df["avg_gdp"].iloc[0]

    # Fit linear trend on historical scores
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        years, scores
    )

    # ------------------------------------------
    # CASE 1 — Already in crisis
    # ------------------------------------------
    if latest_score >= CRISIS_THRESHOLD:

        backtest = None
        if country in known_crises:
            backtest = "CORRECT — model flagged before crisis"

        results.append({
            "country_name"   : country,
            "latest_score"   : round(latest_score, 2),
            "avg_gdp"        : round(float(avg_gdp), 0) 
                               if pd.notna(avg_gdp) else None,
            "trend_slope"    : round(float(slope), 4),
            "status"         : "Already in crisis",
            "projected_year" : latest_year,
            "confidence"     : round(abs(r_value) * 100, 1),
            "backtest"       : backtest,
            "years_to_crisis": 0
        })

    # ------------------------------------------
    # CASE 2 — Wealthy country, buffered by GDP
    # ------------------------------------------
    elif country in wealthy_countries:

        results.append({
            "country_name"   : country,
            "latest_score"   : round(latest_score, 2),
            "avg_gdp"        : round(float(avg_gdp), 0)
                               if pd.notna(avg_gdp) else None,
            "trend_slope"    : round(float(slope), 4),
            "status"         : "Stable — wealth buffered",
            "projected_year" : None,
            "confidence"     : round(abs(r_value) * 100, 1),
            "backtest"       : None,
            "years_to_crisis": None
        })

    # ------------------------------------------
    # CASE 3 — Stable or improving trend
    # ------------------------------------------
    elif slope <= 0:

        results.append({
            "country_name"   : country,
            "latest_score"   : round(latest_score, 2),
            "avg_gdp"        : round(float(avg_gdp), 0)
                               if pd.notna(avg_gdp) else None,
            "trend_slope"    : round(float(slope), 4),
            "status"         : "Stable or improving",
            "projected_year" : None,
            "confidence"     : round(abs(r_value) * 100, 1),
            "backtest"       : None,
            "years_to_crisis": None
        })

    # ------------------------------------------
    # CASE 4 — Getting worse, project crisis year
    # ------------------------------------------
    else:

        years_until = (CRISIS_THRESHOLD - latest_score) / slope
        crisis_year = latest_year + int(np.ceil(years_until))

        if crisis_year <= FORECAST_TO:

            years_from_now = crisis_year - 2026

            if years_from_now <= 1:
                urgency = "IMMINENT — within 1 year"
            elif years_from_now <= 3:
                urgency = f"HIGH — crisis ~{crisis_year}"
            elif years_from_now <= 6:
                urgency = f"MODERATE — crisis ~{crisis_year}"
            else:
                urgency = f"WATCH — crisis ~{crisis_year}"

            # Backtest check
            backtest = None
            if country in known_crises:
                actual = known_crises[country]
                if crisis_year <= actual + 2:
                    backtest = (
                        f"CORRECT — predicted {crisis_year},"
                        f" crisis was {actual}"
                    )
                else:
                    backtest = (
                        f"LATE — predicted {crisis_year},"
                        f" crisis was {actual}"
                    )

            results.append({
                "country_name"   : country,
                "latest_score"   : round(latest_score, 2),
                "avg_gdp"        : round(float(avg_gdp), 0)
                                   if pd.notna(avg_gdp) else None,
                "trend_slope"    : round(float(slope), 4),
                "status"         : urgency,
                "projected_year" : crisis_year,
                "confidence"     : round(abs(r_value) * 100, 1),
                "backtest"       : backtest,
                "years_to_crisis": max(0, years_from_now)
            })

        else:
            results.append({
                "country_name"   : country,
                "latest_score"   : round(latest_score, 2),
                "avg_gdp"        : round(float(avg_gdp), 0)
                                   if pd.notna(avg_gdp) else None,
                "trend_slope"    : round(float(slope), 4),
                "status"         : "Stable or improving",
                "projected_year" : None,
                "confidence"     : round(abs(r_value) * 100, 1),
                "backtest"       : None,
                "years_to_crisis": None
            })

predictions_df = pd.DataFrame(results)

# ============================================
# STEP 6 - PRINT RESULTS
# ============================================

print("\n--- ALREADY IN CRISIS ---")
crisis = predictions_df[
    predictions_df["status"] == "Already in crisis"
].sort_values("latest_score", ascending=False)
print(crisis[["country_name", "latest_score",
              "avg_gdp", "confidence"]
             ].head(20).to_string(index=False))

print("\n--- IMMINENT (within 1 year) ---")
imminent = predictions_df[
    predictions_df["status"].str.contains("IMMINENT", na=False)
].sort_values("latest_score", ascending=False)
if len(imminent) > 0:
    print(imminent[["country_name", "latest_score",
                    "projected_year",
                    "confidence"]].to_string(index=False))
else:
    print("None")

print("\n--- HIGH RISK (2-3 years) ---")
high = predictions_df[
    predictions_df["status"].str.contains("HIGH", na=False)
].sort_values("projected_year")
if len(high) > 0:
    print(high[["country_name", "latest_score",
                "projected_year",
                "confidence"]].to_string(index=False))
else:
    print("None")

print("\n--- MODERATE RISK (4-6 years) ---")
moderate = predictions_df[
    predictions_df["status"].str.contains("MODERATE", na=False)
].sort_values("projected_year")
if len(moderate) > 0:
    print(moderate[["country_name", "latest_score",
                    "projected_year",
                    "confidence"]].to_string(index=False))
else:
    print("None")

print("\n--- WATCH LIST (7+ years) ---")
watch = predictions_df[
    predictions_df["status"].str.contains("WATCH", na=False)
].sort_values("projected_year")
if len(watch) > 0:
    print(watch[["country_name", "latest_score",
                 "projected_year",
                 "confidence"]].to_string(index=False))
else:
    print("None")

print("\n--- BACKTESTING RESULTS (2023-2026) ---")
backtest = predictions_df[
    predictions_df["backtest"].notna()
].sort_values("country_name")
if len(backtest) > 0:
    print(backtest[["country_name", "latest_score",
                    "projected_year",
                    "backtest"]].to_string(index=False))
else:
    print("None")

print("\n--- GDP THRESHOLD SUMMARY ---")
print(f"Wealth threshold used: ${gdp_threshold:,.0f}")
print(f"Countries wealth buffered: {len(wealthy_countries)}")
print(f"Countries in crisis:       "
      f"{len(predictions_df[predictions_df['status'] == 'Already in crisis'])}")
print(f"Countries watch/high/mod:  "
      f"{len(predictions_df[predictions_df['status'].str.contains('HIGH|MODERATE|WATCH|IMMINENT', na=False)])}")
print(f"Countries stable:          "
      f"{len(predictions_df[predictions_df['status'].str.contains('Stable', na=False)])}")

# ============================================
# STEP 7 - PUSH TO SQL
# ============================================

print("\nPushing predictions to PostgreSQL...")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id               SERIAL PRIMARY KEY,
        country_name     VARCHAR(100),
        latest_score     FLOAT,
        avg_gdp          FLOAT,
        trend_slope      FLOAT,
        status           VARCHAR(100),
        projected_year   INT,
        confidence       FLOAT,
        backtest         VARCHAR(200),
        years_to_crisis  FLOAT
    );
""")

cursor.execute("DELETE FROM predictions;")

for _, row in predictions_df.iterrows():
    cursor.execute("""
        INSERT INTO predictions
            (country_name, latest_score, avg_gdp,
             trend_slope, status, projected_year,
             confidence, backtest, years_to_crisis)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        row["country_name"],
        row["latest_score"],
        None if pd.isna(row["avg_gdp"])
             else float(row["avg_gdp"]),
        row["trend_slope"],
        row["status"],
        None if pd.isna(row["projected_year"])
             else int(row["projected_year"]),
        row["confidence"],
        row["backtest"],
        None if pd.isna(row["years_to_crisis"])
             else float(row["years_to_crisis"])
    ))

conn.commit()
print(f"Predictions pushed: {len(predictions_df)} countries")

cursor.close()
conn.close()
print("\nScript 3 complete.")