# BUSA3022 Assignment 2 – Really Big Bank Analytics

**Project Overview**

This project proposes a data pipeline and analytics system for Really Big Bank. It uses two Australian datasets to support market intelligence and dashboard development.

**Data Sources:**
- RBA Cash Rate Target: Historical interest rate data from the Reserve Bank of Australia, Table F1.
- S&P/ASX 200: Historical Australian stock market index data from Yahoo Finance (`^AXJO`).

**Data Pipeline**

The Python proof of concept (POC) demonstrates a repeatable process for reading Excel files, validating records and storing processed data separately from the original files.

The pipeline checks for missing values, duplicate dates and invalid numeric formats. Identified issues are recorded in a separate quality log.


**Repository Files**

| File or Folder | Description |
|---|---|
| `RBA raw data.xlsx` | Original RBA dataset |
| `AXS 200.xlsx` | ASX 200 dataset containing a raw data worksheet |
| `pipeline.py` | Python pipeline implementation |
| `processed/` | Validated CSV datasets |
| `logs/data_quality_log.csv` | Records identified data quality issues |


**How to Run the POC**
1. Download the repository files to your computer.
2. Install Python 3 and the `openpyxl` library.
3. Open the project folder in VS Code.
4. Open a terminal and run:
   `python3 -m pip install openpyxl`
5. Run the pipeline:
   `python3 pipeline.py`
6. Check the generated CSV files in `processed/` and the quality log in `logs/`.


**POC Results**

The initial test produced 3,996 valid RBA records and 255 ASX 200 records. Three quality issues were logged: one missing or invalid RBA cash rate and two missing or invalid ASX 200 volume values.



**Part 2 – Analytical Metrics**

`metrics.py` reads the validated CSVs in `processed/` and builds a curated layer in `curated/` for the dashboard.

| File | Description |
|------|-------------|
| `curated/asx200_daily_metrics.csv` | Daily return, 20/50-day moving averages, trend signal, 20-day volatility, drawdown, average volume and the cash rate in force each trading day |
| `curated/rate_changes.csv` | Every RBA cash rate decision since 2011 with the change in basis points |
| `curated/rate_event_impact.csv` | ASX 200 return 5 trading days before, on the day and 5 days after each decision in the ASX window |
| `curated/kpi_summary.csv` | Headline figures for the dashboard |
| `logs/metrics_notes.csv` | Blank values and why they were left blank |
| `figures/metrics_overview.png` | Chart of the main metrics |

Run after the pipeline: `python3 metrics.py`

POC result: 255 daily metric rows, 38 rate decisions found since 2011, 4 decisions analysed against the ASX 200.

**Limitations**

The POC demonstrates repeatable ingestion from local Excel files, rather than automated downloading from the original providers. Scheduling, automated retries and dashboard integration are proposed components that have not yet been implemented. Missing ASX 200 volume values remain unresolved and should be reviewed before volume-based analysis.
