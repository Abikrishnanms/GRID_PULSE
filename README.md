# GridPulse — Big Data-Driven Household Energy Analytics and Personalised Energy Optimisation Platform

> **Academic Project Status:** The distributed PySpark data-cleaning, deduplication and aggregation pipeline, historical machine learning forecasting models, personalised appliance recommendation engine, energy savings simulator, Starlette REST API, and unified React dashboard are fully implemented and verified. Downstream Apache Kafka streaming, PostgreSQL/TimescaleDB storage, and enterprise Power BI dashboards represent planned architectural extensions.

---

## 1. Project Overview

Residential electricity consumption exhibits substantial temporal variability and complex appliance-level usage dynamics. In typical residential environments, consumers lack visibility into granular consumption drivers and actionable guidance to eliminate energy waste, while grid operators face volatile demand profiles.

GridPulse addresses these challenges as a Big Data-driven household energy analytics and personalised energy optimisation platform. Developed collaboratively by a three-member university engineering team, the platform bridges large-scale distributed smart meter processing with predictive machine learning forecasting, transparent appliance energy profiling, and interactive what-if savings simulations inside a single unified dashboard interface.

### Main Objectives and Capabilities
* **Scalable Data Ingestion & Quality Auditing:** Scalable distributed processing, cleaning, schema validation, and multi-column deduplication of multi-gigabyte smart meter readings.
* **Chronological Demand Forecasting:** Machine learning-based time-series forecasting to establish baseline household consumption and predict demand patterns.
* **Appliance Consumption Profiling:** Mathematical attribution of household electricity consumption by appliance with automatic high-impact load identification.
* **Safety-Constrained Optimization:** Actionable curtailment recommendations with built-in safety suppression for continuous and essential loads (refrigeration, medical equipment).
* **Interactive What-If Simulation:** Pure, non-mutating scenario simulations allowing householders to quantify the energy and financial impacts of behavioral adjustments.

---

## 2. Dataset Information

### Dataset Specifications
* **Dataset Name:** London Smart Meter Energy Consumption Dataset (Low Carbon London project).
* **Primary Source:** UK Power Networks / London Datastore.
* **Dataset Access Link:** [Download/access the dataset](https://drive.google.com/drive/folders/1ZRkrHQ5ZaS8O0L-t6c94bwIi7vaB7cEl?usp=sharing)
* **Raw Filename & Format:** `CC_LCL-FullData.csv` (CSV format, ~7.6 GB uncompressed, ~7.96 GB reported on Google Drive).
* **Temporal Coverage:** Historical half-hourly smart meter readings collected between November 2011 and February 2014. The last complete actual observation used for daily aggregation and modelling is **27 February 2014** (partial readings on 28 February 2014 were dropped during data preparation).

### PySpark Processing Audit
* **Raw Records Processed:** 167,932,474
* **Valid Silver Records:** 167,926,914 (99.9967%)
* **Rejected Malformed Records:** 5,560 (0.0033%, isolated into a quality Parquet layer due to missing or invalid energy readings)
* **Multi-Column Duplicates Removed:** 115,453 (0.0688%, identified via a 4-column composite key grouping)
* **Clean Deduplicated Silver Records:** 167,811,461 ($167,926,914 - 115,453 = 167,811,461$)

### Record Count Discrepancy Note
An initial exploratory inspection via `wc -l` in a local development environment observed 159,394,207 lines (including header), whereas the complete PySpark ingestion job in Google Colab processed 167,932,474 records. This discrepancy represents two separate empirical observations across different execution environments and is documented without speculative explanation.

### Licensing and Data Handling Warning
The dataset is associated with the Low Carbon London project. Because the exact redistribution terms for the hosted Google Drive archive remain unconfirmed, raw data files are excluded from Git version control via `.gitignore` and must not be distributed publicly without confirming licensing terms.

---

## 3. System Architecture

### Target / Planned Architecture (PRD Specification)
```text
Smart Meters ──► Apache Kafka ──► Spark Structured Streaming ──► Data Lake (Bronze/Silver/Gold)
                                                                            │
React Dashboard ◄── TimescaleDB ◄── Savings Simulator ◄── ML Forecaster ◄──┘
```

### Implemented Architecture
```text
[ Big Data Processing Layer (PySpark Batch / Google Colab) ]
  Raw CSV (167.9M rows) ──► Schema Enforcement (FAILFAST) ──► Silver Parquet (167.9M)
                                                                    │
                            Gold Analytical Tables  ◄── Deduplication Engine (167.8M clean)
                            (hourly/daily/household)
                                       │
                                       ▼ (Pre-computed CSV exports)
[ Machine Learning & Analytics Layer (Python) ]
  Prepared Daily Energy (821 days) ──► Random Forest Regressor (Trained Model Artifact)
                                   ├──► 30-Day Recursive Historical Forecaster (28 Feb – 29 Mar 2014)
                                   └──► 5-Origin Rolling Backtesting Engine (150 days)

[ Local Backend REST Service (Starlette + Uvicorn) ]
  POST /api/recommendations ──► Appliance Recommender (Ranking & Safety Suppression)
  POST /api/simulate        ──► Energy Savings Simulator (Non-mutating Scenario Math)

[ Client Dashboard (React 19 + Vite + Recharts) ]
  Historical Trends & Forecast ◄── Static CSV Datasets (/data/)
  Interactive Optimisation UI  ◄── Local REST API (http://127.0.0.1:8000)
```

> [!NOTE]
> **Operational Boundary Clarification:** The PySpark data pipeline operates as an offline batch processing and feature engineering job; it is not continuously streaming data to the dashboard. The React frontend visualizes historical trends and forecasts via pre-computed static CSV exports in `public/data/`, while the recommendation and simulation components query the local Starlette REST API (`127.0.0.1:8000`) on demand. Apache Kafka streaming, PostgreSQL/TimescaleDB persistence, and Power BI enterprise reporting are planned extensions.

---

## 4. Implementation and Key Features

* **Distributed Big Data Pipeline (`notebook/GridPulse_Data_Engineering_Work.ipynb`):** Built with PySpark using a Medallion architecture. Enforces strict schema constraints in `FAILFAST` mode, routes malformed records to a quality audit Parquet store, removes 115,453 duplicate readings via composite key grouping, and aggregates data into Gold analytical tables (`hourly_consumption`, `daily_consumption`, `household_summary`) with automated temporal lag features.
* **Chronological Energy Forecasting (`ml/`):** Prepares 821 clean daily observations with 7-day lag and rolling features. Benchmarks Random Forest against HistGradientBoosting and Seasonal Naive baselines. Persists the trained Random Forest artifact (`random_forest_forecaster.joblib`), produces a 30-day recursive historical forecast (28 February to 29 March 2014), and quantifies error compounding across a 5-origin rolling backtesting framework.
* **Personalised Appliance Recommendation Engine (`recommendation/appliance_recommender.py`):** Calculates 30-day monthly consumption using unrounded formulas, ranks appliances in descending order, tags high-impact loads (contribution ≥ 20.0% or consumption ≥ 30.0 kWh/month), and applies safety suppression rules for continuous devices (refrigerators, freezers, medical units, or ≥ 20 hrs/day) and low-impact appliances (< 5.0% share). Decouples energy and cost: projected energy savings in kWh are always calculated, while monetary savings require a valid user-configured electricity tariff (returning null and displayed as "Unavailable" if unconfigured).
* **Energy Savings Simulator (`recommendation/savings_simulator.py`):** Non-mutating simulation module that recalculates household consumption and projected energy savings in kWh (with monetary savings evaluated when a valid electricity tariff is configured) as users adjust appliance operating hours (0–24 hrs/day) and frequencies (1–7 days/week), enforcing atomic input validation and safety warnings.
* **Backend REST API (`api/main.py`):** Asynchronous API built with Starlette and Uvicorn. Exposes `/api/health`, `/api/recommendations`, and `/api/simulate` with CORS configured for local frontend communication.
* **Unified Client Dashboard (`dashboards/react-dashboard/`):** Responsive single-page application built on React 19, Vite, and Recharts. Combines historical energy KPIs, consumption trends, tariff comparisons, household profile configuration, appliance management, recommendations, what-if simulations, and 30-day forecast visualizations with an event-driven dashboard refresh that dynamically updates analytics when household profile or appliance data changes.

---

## 5. Team Members and Responsibilities

| Team Member | Core Role | Primary Focus Area |
| :--- | :--- | :--- |
| **Abikrishnan M S** | Team Lead / Frontend Development | Unified React 19 dashboard, UI architecture, household profile storage, appliance manager, and client styling. |
| **Krishnendhu** | Data Engineering Lead | PySpark distributed pipeline, schema enforcement, data quality validation, deduplication, and Gold layer feature engineering. |
| **Hemalekshmi** | ML & Optimisation Lead | Energy forecasting models, recursive backtesting, recommendation engine, savings simulator, and Starlette REST API. |

---

## 6. Technology Stack

* **Big Data & Distributed Computing:** Apache Spark (PySpark 4.2.0), Py4J (0.10.9.9), Apache Parquet.
* **Machine Learning & Analytics:** Python 3.10+, Scikit-Learn, Pandas, NumPy, Joblib.
* **Backend REST Service:** Starlette, Uvicorn, Requests.
* **Frontend Web Dashboard:** React (19.3.1), Vite (8.3.5), Recharts (3.10.1), Lucide React (1.64.0).

---

## 7. Installation and Execution

### Prerequisites
* **Python:** 3.10 or higher (tested locally on Python 3.15.0).
* **Node.js & npm:** Node.js 20.19+ or 22.12+ (LTS recommended; Vite 8 requires Node.js 20+).
* **Java Development Kit (JDK):** Java 17 or 21 (required for running PySpark locally; Spark 4.x does not support Java 8 or 11).
* **Git:** Version control client.

### Step-by-Step Setup Commands

```bash
# 1. Clone repository
git clone <REPOSITORY_URL>
cd GRID_PULSE

# 2. Set up Python virtual environment & install dependencies
python -m venv .venv
source .venv/bin/activate       # On Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install starlette uvicorn pandas scikit-learn joblib requests

# 3. Install frontend dependencies
cd dashboards/react-dashboard
npm install
cd ../..

# 4. Execute unit test suite (24 tests)
python -m unittest discover -s recommendation -p "test_*.py" -v

# 5. Start Backend REST API (Terminal 1)
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

# 6. Start Unified Frontend Dashboard (Terminal 2)
cd dashboards/react-dashboard
npm run dev
```

*Access Points:* Open `http://localhost:5173` in a browser for the dashboard, and `http://127.0.0.1:8000/api/health` for the backend health check.

---

## 8. Results and Evaluation

### Big Data Pipeline Processing
* **Throughput:** Scalability benchmarking verified peak observed processing throughput of up to 14.65M rows/second.
* **Data Integrity:** Cleaned and deduplicated 167,932,474 raw rows into 167,811,461 validated Silver records with exact accounting of 5,560 malformed entries and 115,453 duplicate readings.

### Machine Learning Forecasting Evaluation
* **Chronological Split:** 821 prepared daily records partitioned without shuffling into **656 training observations** (2011-11-30 to 2013-09-15) and **165 test observations** (2013-09-16 to 2014-02-27).
* **Single-Step Test Holdout Metrics (165 Observations):**
  * **Random Forest Regressor** ($n=100$, max_depth=8): MAE = **0.3020 kWh/day**, RMSE = **0.3931 kWh/day**, MAPE = **2.81%**, Mean Bias = +0.1327 kWh/day (Note: MAPE is Mean Absolute Percentage Error, not percentage accuracy).
  * **HistGradientBoosting Regressor:** MAE = 0.3268 kWh/day, RMSE = 0.4284 kWh/day, MAPE = 3.00%.
  * **Seasonal Naive Baseline (lag-7):** MAE = 0.4192 kWh/day, RMSE = 0.5615 kWh/day, MAPE = 3.89%.
* **5-Origin Recursive Backtesting (150 Total Predictions across 30-Day Horizons):**
  * Overall recursive performance: MAE = **0.6532 kWh/day**, RMSE = **0.7965 kWh/day**, MAPE = **6.01%**, Mean Bias = +0.5327 kWh/day. Demonstrates expected autoregressive error accumulation over multi-week horizons.

### Optimization Suite & Frontend Verification
* **Unit Test Suite:** All 24 unit tests pass in 0.010s (`recommendation/test_appliance_recommender.py` and `recommendation/test_savings_simulator.py`).
* **Frontend Verification:** Clean ESLint quality audit (0 errors, 0 warnings); production build compiles into 2,614 optimized modules in 1.35s.

---

## 9. Limitations and Future Work

1. **Historical Dataset Scope:** Analysis and forecast models are based on historical London smart meter readings (2011–2014). The 30-day projection represents a 30-day recursive historical forecast (28 February to 29 March 2014) rather than a live operational grid feed.
2. **Recursive Error Accumulation:** Autoregressive multi-step forecasting exhibits compounding error over extended horizons as predicted values replace actual historical lags (MAE increases from 0.52 kWh/day in week 1 to 0.80 kWh/day in week 4).
3. **Appliance Attributions:** Energy attributions rely on user-declared wattage and operational schedules rather than Non-Intrusive Load Monitoring (NILM) hardware sensor telemetry.
4. **Planned Extensions:** Future development goals include implementing real-time Apache Kafka ingestion (`streaming/`), PostgreSQL/TimescaleDB time-series persistence (`database/`), and deploying enterprise Power BI analytical reports.

---

*GridPulse — Big Data Energy Analytics Platform — Academic Engineering Project*
