# GridPulse --- Big Data-Driven Household Energy Analytics and Personalized Energy Optimization Platform

> **Project status:** Foundation and sample data-cleaning pipeline
> implemented. Full-dataset processing and the downstream Kafka,
> streaming, analytics, ML, recommendation, API, database, and dashboard
> components are not yet confirmed complete.

GridPulse aims to build a Big Data-driven household energy analytics and
personalized energy optimization platform. It is being developed by a
three-member team using GitHub and Codex, following an incremental
workflow: **Understand → Ask Codex → Review → Test → Commit → Push →
Integrate**.

The team will first build and understand the shared foundation, then
gradually specialize. Codex is used as a coding assistant; the team
remains responsible for architectural decisions, understanding the code,
testing, and reviewing changes.

## Dataset

### Google Drive dataset link

**Dataset folder/file:** [**https://drive.google.com/drive/folders/1ZRkrHQ5ZaS8O0L-t6c94bwIi7vaB7cEl?usp=sharing**]

Replace the placeholder URL with the Google Drive sharing link for the
dataset. Ensure intended collaborators have permission to access it. Do
not make the dataset public solely for convenience.

### Dataset information

-   **Dataset:** London Smart Meter Energy Consumption Dataset
-   **Expected raw file:** `CC_LCL-FullData.csv`
-   **Format:** CSV
-   **Content:** Historical half-hourly household electricity readings
-   **Size observed in Codespaces:** approximately 7.6 GB
-   **Google Drive size reported:** 7.96 GB
-   **Observed line count:** 159,394,207 lines, including the header
-   **Important:** This is historical data, not a live data feed. If
    used to demonstrate streaming, the records should be described as a
    historical replay or simulated stream.

The Google Drive copy has not yet been confirmed byte-for-byte identical
to the Codespaces copy, and authenticated Drive access from Codespaces
has not yet been configured. Do not download another copy into
Codespaces until the storage approach is decided.

Large datasets and generated outputs are excluded from Git through the
repository's `data/` ignore rule. GitHub is for source code,
documentation, configuration, tests, and Git history---not for storing
the full raw dataset.

## Project Architecture

The project's planned end-to-end architecture, as defined in the team
working guide and PRD, is:

``` text
Data Sources
    |
    v
Kafka
    |
    v
Spark Structured Streaming
    |
    v
Data Lake
    |
    v
Apache Spark Analytics
    |
    v
Analytics / Machine Learning
    |
    v
Recommendations
    |
    v
Savings Engine
    |
    v
PostgreSQL
    |
    v
Power BI
```

The current implemented data-engineering milestone is the initial
foundation:

``` text
Raw Energy CSV
    |
    v
PySpark Reader
    |
    v
Schema / Data-Quality Validation
    |
    +---------------------------+
    |                           |
    v                           v
Valid Records             Rejected Records
    |                           |
    v                           v
Silver Parquet Output     Quality Parquet Output
```

The full architecture is the target design; components should not be
described as implemented until they have been built and tested.

## Current Implementation Status

### Completed and tested

-   Repository structure and development workspace established.
-   PySpark 3.5.6 starts successfully with Java 17 in the current
    Codespaces environment.
-   `spark_jobs/read_energy.py` is available for reading and inspecting
    the energy CSV.
-   `spark_jobs/clean_energy.py` reads a physical sample, standardizes
    columns, parses timestamps and energy values, applies validation
    rules, and writes valid and rejected records to separate Parquet
    outputs.
-   A sample file was created at `data/samples/energy_sample.csv`
    (approximately 498 KB).
-   The sample cleaning run processed 10,000 rows: 9,999 valid and 1
    rejected.
-   The raw `data/` directory is excluded from Git.

### In progress / not yet verified

-   Processing the complete dataset of approximately 159 million
    records.
-   Configuring and testing authenticated Google Drive access from
    Codespaces or selecting another processing environment.
-   Establishing a safe full-data processing plan within available
    storage.
-   Kafka producers/consumers and Spark Structured Streaming.
-   Bronze → Silver → Gold data-lake progression.
-   Household energy analytics and feature engineering.
-   Forecasting and high-consumption detection.
-   Appliance attribution, recommendation and savings engines.
-   PostgreSQL, FastAPI and Power BI integration.
-   Scalability experiments and end-to-end integration.

## Technology Stack

-   Python
-   Apache Spark / PySpark
-   Java 17 for the currently tested Spark environment
-   Parquet
-   Apache Kafka (planned architecture)
-   Spark Structured Streaming (planned architecture)
-   PostgreSQL (planned architecture)
-   FastAPI (planned architecture)
-   Power BI (planned architecture)
-   Git and GitHub
-   Codex as a development assistant
-   Google Drive as a possible location for the large raw dataset; the
    Codespaces connection is still to be configured/tested

The current `requirements.txt` lists `pandas`, `numpy`, `pyspark`,
`pyarrow`, `python-dotenv`, `sqlalchemy`, and `psycopg2-binary`. The
broader architecture may require additional dependencies as modules are
implemented.

## Repository Structure

The current workspace contains these directories (some are still under
development):

``` text
GRID_PULSE/
├── api/
├── config/
├── dashboards/
├── data/                 # Raw/sample data and outputs; ignored by Git
├── database/
├── docs/
├── ml/
├── recommendation/
├── scripts/
├── spark_jobs/
│   ├── read_energy.py
│   └── clean_energy.py
├── streaming/
├── tests/
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

The team guide also proposes `data/raw/`, `data/bronze/`,
`data/silver/`, `data/gold/`, `data/samples/`, and a `docker/` directory
as the intended structure. The repository may evolve toward that
structure as the pipeline develops.

## Getting Started in Codespaces

### Prerequisites

-   Python 3.12 (Python 3.12.3 was observed in the current environment)
-   Java 17
-   Git
-   Access to the dataset
-   Enough free disk space for input and output files

### 1. Open the repository

Open `GRID_PULSE` in GitHub Codespaces, or clone it:

``` bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd GRID_PULSE
```

Replace the placeholder with your actual repository URL.

### 2. Create and activate a virtual environment

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

``` bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Java 17

In the current Codespaces environment, Spark was verified with Java 17:

``` bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
java -version
```

Environment variables may need to be set again in a new terminal.

### 5. Prepare a small sample

If the full CSV is available at `data/CC_LCL-FullData.csv`, create a
sample with the header and first 10,000 data rows:

``` bash
mkdir -p data/samples
head -n 10001 data/CC_LCL-FullData.csv > data/samples/energy_sample.csv
```

The current test pipeline uses this physical sample rather than the full
CSV.

## Run the Current Cleaning Pipeline

### Test mode (default)

``` bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"

python spark_jobs/clean_energy.py
```

Default test paths:

``` text
Input:
data/samples/energy_sample.csv

Valid output:
data/test_silver/energy/

Rejected output:
data/test_quality/rejected_energy/
```

The current script overwrites these test output directories on each run.

### Verified sample result

  Result                Count
  ------------------ --------
  Total processed      10,000
  Valid records         9,999
  Rejected records          1

The rejected sample record had a missing or invalid energy value and
received the reason `missing_or_invalid_energy`.

### Full-data mode --- do not run yet without a storage plan

The script currently supports:

``` bash
export GRIDPULSE_FULL_RUN=1
python spark_jobs/clean_energy.py
```

In full mode, the current script is configured to read
`data/CC_LCL-FullData.csv` and write to `data/silver/energy/` and
`data/quality/rejected_energy/`.

**Do not start the full run in the current Codespace yet.** The raw CSV
is approximately 7.6 GB, the filesystem previously showed about 9 GB
free, and the size of the complete Parquet output is unknown. A
successful full-data run has not yet been demonstrated. The processing
and storage strategy must be reviewed first.

## Current Data-Quality Rules

The current cleaning script assigns the first matching rejection reason:

-   Missing or blank household ID → `missing_household_id`
-   Missing or blank tariff type → `missing_tariff_type`
-   Missing, blank, or invalid timestamp →
    `missing_or_invalid_timestamp`
-   Missing, blank, non-numeric, or NaN energy value →
    `missing_or_invalid_energy`
-   Negative energy value → `negative_energy_value`

The valid Silver output contains:

-   `household_id`
-   `reading_time`
-   `energy_kwh_half_hour`
-   `tariff_type`

Valid records are written as Parquet partitioned by `tariff_type`;
rejected records are written separately for quality review.

## Team Members and Responsibilities

The team guide defines these primary areas. During the initial
foundation stage, all three members should understand the shared
pipeline before working independently.

### Abikrishnan M S --- Team Lead

-   Overall architecture and Git/GitHub management
-   Dataset integration and PySpark
-   Data cleaning, Data Lake and Parquet
-   Spark transformations and feature engineering
-   Scalability experiments and final integration

### Krishnendhu --- Team Member

-   Kafka producer and consumer
-   Spark Structured Streaming
-   Energy forecasting
-   High-consumption detection
-   Machine-learning evaluation

### Hemalekshmi --- Team Member

-   Household energy fingerprint
-   Appliance attribution
-   Recommendation engine and savings engine
-   PostgreSQL
-   FastAPI
-   Power BI support

## Team Development Workflow

The team uses individual branches and reviews changes before
integration. **Do not experiment directly on `main`.**

The intended flow is:

``` text
Individual member branch
        |
        v
Implement a small task
        |
        v
Understand and review code
        |
        v
Run tests
        |
        v
Review Git diff
        |
        v
Commit and push
        |
        v
Team review / pull request
        |
        v
develop
        |
        v
Final testing
        |
        v
main
```

The guide names the branches `abikrishnan`, `krishnendhu`, and
`hemalekshmi`, with work integrated into `develop` and then promoted to
`main` after final testing. Use the branch names and policies currently
configured in the actual repository.

For each task, report: - **DONE:** what was completed - **FILES:** files
created or modified - **TEST:** commands/tests and results -
**PROBLEM:** issues encountered - **NEXT:** proposed next step

### Example commit workflow

Review the branch and changed files first:

``` bash
git status
git diff
```

Then stage only the intended files, review the staged changes, and
commit:

``` bash
git add README.md spark_jobs/ requirements.txt .gitignore
git diff --cached
git commit -m "docs: document GridPulse project workflow"
git push origin <YOUR_BRANCH_NAME>
```

Replace `<YOUR_BRANCH_NAME>` with your current branch. Do not blindly
use `git add .`; verify that no secrets, raw datasets, or generated
outputs are staged.

## Git and Dataset Safety

-   Do not commit the full CSV or large generated Parquet data to
    GitHub.
-   Keep `.env`, API keys, passwords, database credentials and access
    tokens out of Git.
-   Use `.env.example` with placeholders when configuration
    documentation is needed.
-   Check ignored files and staged changes before committing:

``` bash
git check-ignore -v data/CC_LCL-FullData.csv
git status --short
git diff --cached
```

## Current Blocker: Full-Dataset Processing and Storage

The current Codespace previously reported a 32 GB filesystem with
approximately 9 GB available. The raw CSV alone is approximately 7.6 GB.
The complete output size is unknown, so a full run could exhaust disk
space.

The user has a Google Drive copy reported as 7.96 GB, but the file has
not been verified as identical to the Codespaces copy and direct
authenticated access from Codespaces has not yet been configured. Do not
download another full copy into the Codespace.

Possible approaches to evaluate: - Authenticated remote access to Google
Drive from Codespaces, if supported and reliable for Spark. - Processing
through Google Colab with Drive mounted, while keeping source code in
GitHub. - A machine or storage environment with more available disk
space.

Any chosen approach should first be tested on a small sample and should
account for storage, memory, remote I/O, and session limitations.

## Next Steps

-   [ ] Confirm the preferred authenticated way to access the Drive
    dataset.
-   [ ] Choose a full-data processing environment with sufficient
    storage.
-   [ ] Review the cleaning script for repeated full-data scans and safe
    output behavior.
-   [ ] Test the selected approach on a bounded sample.
-   [ ] Process the complete dataset and validate accepted/rejected
    counts.
-   [ ] Continue Bronze → Silver → Gold data-lake development.
-   [ ] Implement Kafka and Spark Structured Streaming according to the
    PRD.
-   [ ] Develop energy analytics, forecasting, high-consumption
    detection, recommendations, savings, PostgreSQL/FastAPI, and Power
    BI modules.
-   [ ] Add automated tests, scalability experiments, and integration
    documentation.

## Dataset Attribution and License

Before publishing the repository publicly, add the official dataset
source, attribution, and applicable licence/usage terms. Do not assume
that the ability to download a dataset automatically permits
unrestricted redistribution.
