import psycopg2
import pandas as pd
from fuzzywuzzy import process
import pycountry
from config import DB_CONFIG

# ============================================
# STEP 1 - CONNECT TO DATABASE
# ============================================

conn = psycopg2.connect(
    host=DB_CONFIG["host"],
    port=DB_CONFIG["port"],
    database=DB_CONFIG["database"],
    user=DB_CONFIG["user"],
    password=DB_CONFIG["password"]
)
cursor = conn.cursor()
print("Connected successfully")

# ============================================
# STEP 2 - BUILD STANDARD COUNTRY NAME LIST
# ============================================

# This gives us the official list of all country names
standard_countries = [country.name for country in pycountry.countries]
print(f"Standard country list loaded: {len(standard_countries)} countries")

# ============================================
# STEP 3 - FUNCTION TO STANDARDIZE ONE NAME
# ============================================

def standardize_name(name, standard_list, threshold=80):
    """
    Takes a country name and finds the closest
    match in the official standard list.
    threshold=80 means 80% similar = match
    """
    if not name or pd.isna(name):
        return name
    
    match, score = process.extractOne(name, standard_list)
    
    if score >= threshold:
        return match
    else:
        # If no good match found, keep original
        return name

# ============================================
# STEP 4 - LOAD ALL TABLES INTO PYTHON
# ============================================

print("\nLoading tables from PostgreSQL...")

gdp_df = pd.read_sql("SELECT * FROM gdp", conn)
rainfall_df = pd.read_sql("SELECT * FROM rainfall", conn)
crop_yield_df = pd.read_sql("SELECT * FROM crop_yield", conn)
conflict_df = pd.read_sql("SELECT * FROM conflict", conn)
import_dep_df = pd.read_sql("SELECT * FROM import_dependency", conn)

print(f"GDP rows loaded:               {len(gdp_df)}")
print(f"Rainfall rows loaded:          {len(rainfall_df)}")
print(f"Crop yield rows loaded:        {len(crop_yield_df)}")
print(f"Conflict rows loaded:          {len(conflict_df)}")
print(f"Import dependency rows loaded: {len(import_dep_df)}")

# ============================================
# STEP 5 - STANDARDIZE COUNTRY NAMES
# ============================================

print("\nStandardizing country names...")
print("This may take 2-3 minutes, please wait...")

gdp_df["country_name"] = gdp_df["country_name"].apply(
    lambda x: standardize_name(x, standard_countries)
)
print("GDP done")

rainfall_df["country_name"] = rainfall_df["country_name"].apply(
    lambda x: standardize_name(x, standard_countries)
)
print("Rainfall done")

crop_yield_df["country_name"] = crop_yield_df["country_name"].apply(
    lambda x: standardize_name(x, standard_countries)
)
print("Crop yield done")

conflict_df["country_name"] = conflict_df["country_name"].apply(
    lambda x: standardize_name(x, standard_countries)
)
print("Conflict done")

import_dep_df["country_name"] = import_dep_df["country_name"].apply(
    lambda x: standardize_name(x, standard_countries)
)
print("Import dependency done")

# ============================================
# STEP 6 - CHECK RESULTS BEFORE SAVING
# ============================================

print("\nSample of standardized GDP country names:")
print(gdp_df["country_name"].unique()[:20])

print("\nSample of standardized conflict country names:")
print(conflict_df["country_name"].unique()[:20])

# ============================================
# STEP 7 - PUSH CLEANED DATA BACK TO POSTGRESQL
# ============================================

print("\nPushing cleaned data back to PostgreSQL...")

def push_back_to_sql(df, table_name, cursor, conn):
    # Clear the existing table
    cursor.execute(f"DELETE FROM {table_name};")
    
    # Insert cleaned rows one by one
    for _, row in df.iterrows():
        columns = ", ".join(row.index)
        values = tuple(row.values)
        placeholders = ", ".join(["%s"] * len(row))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)
    
    conn.commit()
    print(f"{table_name} pushed back successfully — {len(df)} rows")

push_back_to_sql(gdp_df, "gdp", cursor, conn)
push_back_to_sql(rainfall_df, "rainfall", cursor, conn)
push_back_to_sql(crop_yield_df, "crop_yield", cursor, conn)
push_back_to_sql(conflict_df, "conflict", cursor, conn)
push_back_to_sql(import_dep_df, "import_dependency", cursor, conn)

# ============================================
# STEP 8 - VERIFY MISMATCHES ARE REDUCED
# ============================================

print("\nChecking remaining mismatches...")

gdp_countries = set(pd.read_sql(
    "SELECT DISTINCT country_name FROM gdp", conn
)["country_name"])

conflict_countries = set(pd.read_sql(
    "SELECT DISTINCT country_name FROM conflict", conn
)["country_name"])

import_countries = set(pd.read_sql(
    "SELECT DISTINCT country_name FROM import_dependency", conn
)["country_name"])

only_in_gdp = gdp_countries - conflict_countries
only_in_conflict = conflict_countries - gdp_countries
only_in_import = import_countries - gdp_countries

print(f"Countries in GDP not in conflict:          {len(only_in_gdp)}")
print(f"Countries in conflict not in GDP:          {len(only_in_conflict)}")
print(f"Countries in import dep not in GDP:        {len(only_in_import)}")

# ============================================
# STEP 9 - CLOSE CONNECTION
# ============================================

cursor.close()
conn.close()
print("\nScript 1 complete. Country names standardized.")