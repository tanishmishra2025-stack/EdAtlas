# EdAtlas — U.S. Higher Education ETL Pipeline

EdAtlas is an end-to-end Python data engineering project that ingests higher education institution data from the U.S. Department of Education's College Scorecard API, transforms and validates the data, and loads it into PostgreSQL for SQL analytics.

## Technology Stack

Python 3.12 · pandas · PostgreSQL 17 · SQLAlchemy · psycopg · Docker · pytest · uv

## Pipeline Architecture

```text
College Scorecard REST API
          |
          v
Paginated Data Extraction
          |
          v
Raw JSON
          |
          v
Transformation (pandas)
          |
          v
Data Curation
          |
          v
Data Quality Validation
          |
          v
Transactional PostgreSQL Loading
          |
          v
SQL Analytics
```

## Key Features

- Retrieves paginated institution records through the College Scorecard API.
- Verifies API-reported record totals and unique school identifiers.
- Cleans and normalizes 14 source fields using pandas.
- Produces curated datasets with derived admission and completion percentages.
- Validates required fields, duplicate identifiers, numeric ranges, and source-data anomalies.
- Uses transactional staging and refresh operations to load PostgreSQL.
- Supports both live API ingestion and local JSON processing.
- Provides SQL analytics for institutions by state, net prices, and earnings-to-price comparisons.
- Includes automated tests for transformation, curation, validation, and transaction rollback behavior.

## Verified Results

| Metric | Result |
|---|---|
| Institutions processed | 6,273 |
| Unique school IDs | 6,273 |
| Data validation errors | 0 |
| Source-data warnings | 12 |
| Automated tests passing | 18 |

These figures represent one verified pipeline execution and may change as source data is updated.

## Project Structure

```text
EdAtlas/
├── src/edatlas/
│   ├── ingestion/
│   ├── transformation/
│   ├── quality/
│   ├── loading/
│   └── pipeline.py
├── sql/
├── tests/
├── data/                   # Generated datasets (not committed)
├── pyproject.toml
├── uv.lock
├── .env.example
└── README.md
```

## Installation

Requirements:

- Python 3.12 or newer
- uv package manager
- PostgreSQL 17 (locally or through Docker)
- College Scorecard API key

Install dependencies:

```bash
uv sync
```

Copy `.env.example` to `.env` and provide the appropriate API key and PostgreSQL connection settings.

The destination PostgreSQL table and database must already be initialized with the expected schema.

## Running the Pipeline

For live API ingestion, set:

```text
EDATLAS_USE_LOCAL_DATA=0
```

For local JSON input, set:

```text
EDATLAS_USE_LOCAL_DATA=1
```

Then execute:

```bash
uv run python -m edatlas.pipeline
```

The local mode requires an existing raw JSON dataset.

## Testing

Run the full test suite:

```bash
uv run pytest -v
```

The current suite contains 18 tests. Database-dependent transaction testing requires an accessible PostgreSQL instance.

## SQL Analytics

The `sql/` directory contains:

1. `01_colleges_by_state.sql` — Institution distribution by state.
2. `02_average_net_price_by_state.sql` — Average reported net prices by state.
3. `03_earnings_price_comparison.sql` — Descriptive earnings-to-price comparison.

The earnings-to-price ratio is not a formal return-on-investment measure.

## Known Limitations

- Some source data fields contain missing or unusual values.
- Database initialization is not yet automated.
- Retries, backoff, and API resilience can be improved.
- Dedicated integration tests for the loading function are planned.
- Continuous integration and automated deployment are future improvements.

## Data Source

U.S. Department of Education — College Scorecard

https://collegescorecard.ed.gov/data/

## Purpose

This project demonstrates practical data engineering skills in API ingestion, ETL development, data quality validation, relational databases, transaction handling, SQL analytics, and automated testing.