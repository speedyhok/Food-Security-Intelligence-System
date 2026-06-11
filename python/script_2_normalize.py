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
# STEP 2 - LOAD MASTER VIEW
# ============================================

df = pd.read_sql("SELECT * FROM master_food_security", conn)
print(f"Rows loaded: {len(df)}")

# ============================================
# STEP 3 - HANDLE MISSING VALUES
# ============================================

# Conflict missing = 0 (no recorded events = peaceful)
df["conflict_score"] = df["conflict_score"].fillna(0)

# Others = fill with that year's global average
for col in ["rainfall_mm", "yield_per_hectare",
            "import_dependency_percent"]:
    df[col] = df.groupby("year")[col].transform(
        lambda x: x.fillna(x.mean())
    )

print(f"Remaining nulls: {df.isnull().sum().sum()}")

# ============================================
# STEP 4 - NORMALIZE WITHIN YEAR
# (Fix 1 — compare countries to peers same year)
# ============================================

print("\nApplying within-year normalization...")

def normalize_within_year(df, col):
    """
    Ranks each country against peers in the SAME year
    not against all countries across all years
    """
    return df.groupby("year")[col].rank(pct=True) * 100

# Higher value = higher risk
df["conflict_norm"] = normalize_within_year(df, "conflict_score")
df["import_norm"]   = normalize_within_year(df, "import_dependency_percent")

# Lower value = higher risk — invert
df["rainfall_norm"] = 100 - normalize_within_year(df, "rainfall_mm")
df["yield_norm"]    = 100 - normalize_within_year(df, "yield_per_hectare")
df["gdp_norm"]      = 100 - normalize_within_year(df, "gdp_per_capita")

# Price normalized within year
df["price_norm"]    = normalize_within_year(df, "cereals_price_index")

print("Within-year normalization complete")

# ============================================
# STEP 5 - PRICE WEIGHTED BY IMPORT DEPENDENCY
# (Fix 2 — price shocks hurt importers more)
# ============================================

print("Applying price-import interaction...")

df["price_adjusted"] = (
    df["price_norm"] * (df["import_norm"] / 100)
)

# Rescale back to 0-100
price_min = df["price_adjusted"].min()
price_max = df["price_adjusted"].max()
df["price_adjusted"] = (
    (df["price_adjusted"] - price_min) /
    (price_max - price_min)
) * 100

print("Price adjustment complete")

# ============================================
# STEP 6 - CALCULATE RAW RISK SCORE
# ============================================

print("Calculating risk scores...")

df["raw_score"] = (
    (df["yield_norm"]     * 0.25) +
    (df["conflict_norm"]  * 0.25) +
    (df["rainfall_norm"]  * 0.20) +
    (df["price_adjusted"] * 0.15) +
    (df["import_norm"]    * 0.10) +
    (df["gdp_norm"]       * 0.05)
)

# ============================================
# STEP 7 - GDP DAMPENING
# (Fix 3 — wealthy countries absorb shocks better)
# ============================================

print("Applying GDP dampening...")

def gdp_dampener(gdp_norm_score):
    """
    Countries with low GDP norm (wealthy countries
    have low gdp_norm because we inverted it)
    get their scores reduced.

    gdp_norm low  = wealthy country = dampener < 1
    gdp_norm high = poor country    = dampener > 1
    """
    # Scale between 0.6 (very rich) and 1.4 (very poor)
    return 0.6 + (gdp_norm_score / 100) * 0.8

df["dampener"]    = df["gdp_norm"].apply(gdp_dampener)
df["final_score"] = (df["raw_score"] * df["dampener"])

# Cap at 100
df["final_score"] = df["final_score"].clip(0, 100).round(2)

# ============================================
# STEP 8 - CLASSIFY RISK LEVEL
# ============================================

def classify_risk(score):
    if score <= 30:
        return "Green"
    elif score <= 60:
        return "Orange"
    else:
        return "Red"

df["risk_level"] = df["final_score"].apply(classify_risk)

print("\nRisk level distribution:")
print(df["risk_level"].value_counts())

print("\nTop 20 highest risk countries 2022:")
latest = df[df["year"] == 2022].nlargest(20, "final_score")
print(latest[["country_name", "final_score",
              "risk_level"]].to_string(index=False))

print("\nBottom 10 lowest risk countries 2022:")
bottom = df[df["year"] == 2022].nsmallest(10, "final_score")
print(bottom[["country_name", "final_score",
              "risk_level"]].to_string(index=False))

print("\nValidation — known crisis countries:")
validation = ["Sudan", "Yemen", "Afghanistan",
              "Syria", "South Sudan", "Mali",
              "Niger", "Burkina Faso", "Chad"]

for country in validation:
    data = df[df["country_name"] == country]
    if len(data) > 0:
        avg  = data["final_score"].mean().round(2)
        risk = data["risk_level"].mode()[0]
        print(f"  {country:20s} avg {avg:5.1f}  {risk}")
    else:
        print(f"  {country:20s} not found")

print("\nValidation — should be Green/low:")
stable = ["Germany", "France", "United States",
          "Canada", "Australia", "Norway",
          "Singapore", "Japan"]

for country in stable:
    data = df[df["country_name"] == country]
    if len(data) > 0:
        avg  = data["final_score"].mean().round(2)
        risk = data["risk_level"].mode()[0]
        print(f"  {country:20s} avg {avg:5.1f}  {risk}")
    else:
        print(f"  {country:20s} not found")

# ============================================
# STEP 9 - PUSH TO SQL
# ============================================

cursor = conn.cursor()
cursor.execute("DELETE FROM risk_scores;")

for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO risk_scores
            (country_name, year, final_score, risk_level,
             yield_norm, conflict_norm, rainfall_norm,
             price_norm, import_norm, gdp_norm)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        row["country_name"],
        int(row["year"]),
        float(row["final_score"]),
        row["risk_level"],
        float(row["yield_norm"]),
        float(row["conflict_norm"]),
        float(row["rainfall_norm"]),
        float(row["price_adjusted"]),
        float(row["import_norm"]),
        float(row["gdp_norm"])
    ))

conn.commit()
print(f"\nRisk scores pushed: {len(df)} rows")

cursor.close()
conn.close()
print("Script 2 complete.")