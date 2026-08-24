# Pricing Control Tower — Data Layer

_Last verified: 2026-08-24_

This directory contains the analytical transformation pipeline (dbt), the source-data acquisition pipeline (Scrapy scraping + transformation), and the Python scripts used to seed/reset the transactional database with generated data.

## Tech stack

From `data/pyproject.toml` (Python `>=3.12`):

- **Scrapy** — web scraping framework
- **dbt-postgres** (`dbt-core` + Postgres adapter) — SQL transformation pipeline
- **psycopg / psycopg-binary** — direct PostgreSQL access from the generation/seed scripts

## Project structure

```text
data/
├── dbt/                       # dbt project "pct_analytics" (profile "pct")
│   ├── dbt_project.yml
│   └── models/
│       ├── staging/            # stg_country, stg_price, stg_product, stg_product_family,
│       │                       #   stg_promotion, stg_sales, stg_store (+ sources.yml, stg.yml)
│       ├── intermediate/       # int_sales_enriched.sql
│       └── marts/              # obt_sales, kpi_price_performance, kpi_promo_performance
├── scraping/                   # Scrapy project "product_catalog"
│   └── product_catalog/
│       └── spiders/fitnessboutique_spider.py   # scrapes the FitnessBoutique catalog
├── transformation/
│   └── transform_scraped_products.py           # raw scraped JSON -> product/price/product_family seed data
├── scripts/                    # DB seeding and data-generation scripts (see below)
├── raw/                        # scraped output, e.g. fitnessboutique_products.json
├── processed/                  # transformed JSON ready for loading (products, prices, product_families, product_images)
└── pyproject.toml
```

## Data acquisition (scraping)

The initial product catalog is scraped from FitnessBoutique via Scrapy (`data/scraping/product_catalog/spiders/fitnessboutique_spider.py`), producing `data/raw/fitnessboutique_products.json`. `data/transformation/transform_scraped_products.py` then validates and maps this raw data into `data/processed/` (products, prices, product_families, product_images), ready to be loaded into `pct_core`.

## Scripts (`data/scripts/`)

- `reset_and_seed.py` — full database reset and initial seeding (loads processed catalog data, generates historical sales).
- `generate_incremental_sales.py` — generates incremental daily sales transactions.
- `generate_anomaly_scenarios.py` — generates targeted pricing/sales anomaly scenarios calibrated against the real organic baseline (used to validate the anomaly-detection features).
- `load_products_only.py` — loads only the product catalog without sales.
- `fix_prices_effective_from.py` — one-off data-fix script for price effective dates.
- `_db.py` — shared DB connection helper for the scripts above.

## dbt pipeline

The dbt project (`data/dbt/`, project name `pct_analytics`, profile `pct`) reads from `pct_core` and builds the `pct_analytics` schema through a staging → intermediate → marts pipeline:

```bash
cd data/dbt
dbt run
dbt test
```

## Note

`data/main.py` is an unused uv-generated stub (`print("Hello from data!")`) and is not an actual entry point — use the scripts under `data/scripts/`, the Scrapy project under `data/scraping/`, or `dbt` commands under `data/dbt/` instead.