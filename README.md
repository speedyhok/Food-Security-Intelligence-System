# 🌍 Food Security Intelligence System

> An end-to-end data intelligence system that scores, predicts, backtests and simulates food crisis risk across 150+ countries using real-world data from the World Bank, FAO, UN and ACLED.

---

## 📊 Live Dashboard

> Built in Power BI — 6 interactive pages covering historical risk, country deep dives, crisis predictions, early warning signals, population exposure and cross-border contagion mapping.

---

## 🎯 What This Project Does

This system answers four questions that matter to analysts, policymakers and researchers:

| Question | How |
|---|---|
| Which countries are at risk right now? | 6-variable weighted risk index |
| Why are they at risk? | Factor breakdown per country |
| Who will hit crisis and when? | Linear regression forecast to 2035 |
| Who is silently deteriorating? | Early warning deterioration detection |
| How many people are affected? | Population-scaled exposure model |
| How does crisis spread? | Regional contagion vulnerability model |

---

## 🏆 Key Achievements

- **13/13 backtesting accuracy** — model correctly flagged all known food crises (Sudan 2023, Niger 2023, Sri Lanka 2022, Ethiopia 2023, Haiti 2024 and 8 more) using only pre-crisis data
- **3.42 billion people** quantified as food insecure or at risk globally
- **150+ countries** scored annually across 2010–2022
- **6 Python scripts** fully automating data cleaning, scoring, prediction and database management
- **Data-driven GDP threshold** ($14,062) automatically separating structural vulnerability from active crisis — no hardcoded country lists
- **Within-year percentile normalization** controlling for global temporal shifts including the 2022 Ukraine war food price spike
- Predictions extended to **2035** with 5 urgency tiers

---

## 🗂️ Project Architecture

```
Raw Data (World Bank + FAO + UN + ACLED)
              ↓
     Excel → Clean + Merge
              ↓
     PostgreSQL → Structured Database
              ↓
         Python Layer
    ┌─────────────────────┐
    │  Risk Score Engine  │
    │  Crisis Predictions │
    │  Early Warning      │
    │  Backtesting        │
    │  Population Scaling │
    │  Contagion Model    │
    └─────────────────────┘
              ↓
     Power BI → 6-Page Dashboard
```

---

## 📐 Risk Score Formula

```
Risk Score =
  Crop Yield Decline     × 25%
+ Conflict Score         × 25%
+ Rainfall Deficit       × 20%
+ Cereals Price Index    × 15%
+ Import Dependency      × 10%
+ Low GDP Per Capita     ×  5%

Score 0–30  → Green  (Safe)
Score 31–60 → Orange (Moderate Risk)
Score 61–100→ Red    (High Risk)
```

**Three model improvements over baseline:**
1. Within-year percentile normalization (controls for global temporal shifts)
2. Cereals price weighted by import dependency (price shocks hurt importers more)
3. GDP dampening interaction term (separates structural vulnerability from active crisis)

---

## 🗄️ Database Schema

```sql
gdp                  → country_name, year, gdp_per_capita
rainfall             → country_name, year, rainfall_mm
crop_yield           → country_name, year, yield_per_hectare
food_prices          → year, cereals_price_index
import_dependency    → country_name, year, import_dependency_percent
conflict             → country_name, year, conflict_score
master_food_security → joined view of all 6 variables
risk_scores          → country_name, year, final_score, risk_level
predictions          → country_name, status, projected_year, confidence, backtest
early_warning        → country_name, severity, variables_worsening, score_change_3yr
population_exposure  → country_name, people_at_risk, exposure_level
contagion            → country_name, region, contagion_score, contagion_level
```

---

## 🐍 Python Scripts

| Script | Purpose |
|---|---|
| script_1_clean.py | Fuzzy country name standardization across all tables |
| script_2_normalize.py | Within-year normalization, GDP dampening, risk scoring |
| script_3_predict.py | Linear regression crisis timeline forecasting to 2035 |
| script_4_early_warning.py | Consecutive deterioration detection across 6 variables |
| script_5_population.py | Population exposure scaling and human impact quantification |
| script_6_contagion.py | Regional food supply chain contagion vulnerability model |

---

## 📈 Dashboard Pages

| Page | Purpose |
|---|---|
| World Risk Map | Choropleth world map with year slicer 2010–2022 |
| Country Deep Dive | Full variable breakdown and trend for any selected country |
| Crisis Predictions | Forecast timeline to 2035 with backtesting validation |
| Early Warning System | Hidden deterioration detection in currently safe countries |
| Population Exposure | Human scale — 3.42B people quantified by risk level |
| Contagion Risk | Cross-border vulnerability if regional food producers collapse |

---

## 📦 Data Sources

| Dataset | Source | Variables |
|---|---|---|
| GDP Per Capita | World Bank | Economic capacity |
| Annual Rainfall | World Bank | Climate vulnerability |
| Cereal Crop Yield | FAO FAOSTAT | Food production |
| Cereals Price Index | FAO World Food Situation | Food affordability |
| Cereal Import Dependency | FAO FAOSTAT | Supply chain risk |
| Conflict Events | ACLED | Instability risk |

---

## ⚙️ Tech Stack

```
Data Cleaning    → Microsoft Excel (Power Query)
Database         → PostgreSQL
Query Language   → SQL
Scripting        → Python 3
Libraries        → pandas, numpy, psycopg2, scipy, fuzzywuzzy, pycountry
Visualization    → Microsoft Power BI
Version Control  → Git + GitHub
```

---

## 🚀 How To Run This Project

### Prerequisites
```bash
pip install psycopg2-binary pandas numpy scipy sqlalchemy fuzzywuzzy python-Levenshtein pycountry
```

### Setup
```bash
# 1. Clone the repository
git clone https://github.com/yourusername/food-security-intelligence

# 2. Create PostgreSQL database
createdb food_security_db

# 3. Configure connection
# Edit config.py with your database credentials

# 4. Import cleaned Excel data into PostgreSQL tables

# 5. Run scripts in order
python script_1_clean.py
python script_2_normalize.py
python script_3_predict.py
python script_4_early_warning.py
python script_5_population.py
python script_6_contagion.py

# 6. Open Food_crisis.pbix in Power BI Desktop
# 7. Refresh data connection
```

---

## 🔍 Model Validation

The model was backtested against 13 known real-world food crises occurring between 2023 and 2026:

| Country | Crisis Year | Model Prediction | Result |
|---|---|---|---|
| Sudan | 2023 | Already flagged Red | ✅ CORRECT |
| Niger | 2023 | Already flagged Red | ✅ CORRECT |
| Mali | 2023 | Already flagged Red | ✅ CORRECT |
| Burkina Faso | 2023 | Already flagged Red | ✅ CORRECT |
| Ethiopia | 2023 | Already flagged Red | ✅ CORRECT |
| Chad | 2023 | Already flagged Red | ✅ CORRECT |
| Yemen | 2023 | Already flagged Red | ✅ CORRECT |
| Afghanistan | 2023 | Already flagged Red | ✅ CORRECT |
| Syria | 2023 | Already flagged Red | ✅ CORRECT |
| South Sudan | 2023 | Already flagged Red | ✅ CORRECT |
| Zimbabwe | 2024 | Already flagged Red | ✅ CORRECT |
| Mozambique | 2024 | Already flagged Red | ✅ CORRECT |
| Haiti | 2024 | Already flagged Red | ✅ CORRECT |

**Accuracy: 13/13 (100%)**

---

## ⚠️ Known Limitations

- Somalia excluded due to insufficient data reporting across all source datasets — a known limitation reflecting long-term institutional instability
- Data coverage ends at 2022 — predictions are forward projections from this baseline
- Contagion model uses regional food network approximations rather than bilateral trade flow data
- Small island nations may score high due to structural import dependency despite political stability
- North Korea and Taiwan excluded due to data unavailability in World Bank and FAO sources

---

## 📁 Repository Structure

```
food-security-intelligence/
│
├── 1_Raw_Data/          Raw downloaded datasets
├── 2_Cleaned_Data/      Excel cleaned files
├── 3_Master_File/       Merged master Excel file
├── 4_SQL/               Database schema and queries
├── 5_Python/            All 6 Python scripts
│   ├── config.py
│   ├── script_1_clean.py
│   ├── script_2_normalize.py
│   ├── script_3_predict.py
│   ├── script_4_early_warning.py
│   ├── script_5_population.py
│   └── script_6_contagion.py
├── 6_PowerBI/           Power BI dashboard file
│   └── Food_crisis.pbix
└── README.md
```

---

## 👤 Author Speedyhok

Built as a portfolio project demonstrating end-to-end data analytics capabilities across Excel, SQL, Python and Power BI using real-world humanitarian datasets.
