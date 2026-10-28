# NBP Lakehouse

![CI](https://github.com/Rossi2882/nbp-lakehouse/actions/workflows/ci.yml/badge.svg)

A data platform for **NBP (National Bank of Poland) exchange rates and gold prices**: daily ingestion from the public NBP API, a lakehouse with bronze/silver/gold layers, orchestration and CI/CD.

> 🚧 Work in progress – built in stages. See the roadmap below.

## Architecture (target)

```
NBP Web API ──► Python ingest ──► BRONZE (raw JSON, ADLS Gen2)
                                     │  PySpark on Azure Databricks
                                     ▼
                                  SILVER (Delta Lake, cleaned, incremental MERGE)
                                     │  dbt (dbt-databricks) + data tests
                                     ▼
                                  GOLD (financial metrics) ──► Power BI dashboard

Orchestration: Apache Airflow · CI/CD: GitHub Actions · Infra: Azure
```

## Roadmap

- [x] **Stage 1 – Ingest → bronze:** NBP API client (exchange rate tables A/B/C, gold prices), automatic splitting of long date ranges, retries, raw JSON written to the bronze layer, unit tests, CI
- [ ] **Stage 2 – Silver:** PySpark transformations to Delta Lake, incremental `MERGE`, tests
- [ ] **Stage 3 – Gold:** dbt models (daily/monthly changes, moving averages, volatility, cross rates, gold in EUR/USD), dbt tests and docs
- [ ] **Stage 4 – Orchestration:** Airflow DAG (ingest → Spark → dbt → tests), backfill
- [ ] **Stage 5 – Azure:** ADLS Gen2 + Azure Databricks, Key Vault, deployment with Databricks Asset Bundles (dev/prod)
- [ ] **Stage 6 – Power BI dashboard** and final documentation

## Data source

[NBP Web API](https://api.nbp.pl/) – public, no authentication.

| Dataset | Endpoint | Available from | Max range per request |
|---|---|---|---|
| Exchange rates, tables A/B/C | `/exchangerates/tables/{table}/{start}/{end}/` | 2002 | 93 days |
| Gold price (PLN per 1 g) | `/cenyzlota/{start}/{end}/` | 2013 | 367 days |

The API returns `404` for ranges without data (weekends, public holidays) – the client treats it as an empty result.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env

# Ingest Q1 2024 average rates (table A) and gold prices into ./data/bronze
nbp-ingest --dataset rates_a --start 2024-01-01 --end 2024-03-31
nbp-ingest --dataset gold    --start 2024-01-01 --end 2024-03-31
```

Bronze layout:

```
data/bronze/<dataset>/ingest_date=YYYY-MM-DD/<dataset>_<start>_<end>.json
```

Each file keeps the raw API payload unchanged inside an envelope with metadata (`range_start`, `range_end`, `ingested_at`, `record_count`), so it can always be reprocessed.

## Development

```bash
ruff check . && ruff format --check .   # lint
pytest -v                               # unit tests (API mocked with `responses`)
```

CI runs both on every push and pull request (Python 3.11 and 3.12).

## Project structure

```
src/nbp_lakehouse/
  config.py              settings and NBP API constants
  ingest/
    dates.py             splitting date ranges into API-sized chunks
    nbp_client.py        HTTP client with retries and error handling
    bronze_writer.py     raw JSON + metadata → bronze layer
    run_ingest.py        CLI entry point (nbp-ingest)
tests/                   unit tests
dbt/                     (stage 3)
airflow/dags/            (stage 4)
docs/                    diagrams and screenshots
```
