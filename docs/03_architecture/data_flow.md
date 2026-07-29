# Data Flow — Pricing Control Tower

## 1. Data Flow Overview

```
┌───────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Python Scripts   │────▶│   pct_core       │────▶│   pct_analytics     │
│  (data/scripts/)  │     │   (PostgreSQL)   │     │   (dbt views)       │
└───────────────────┘     └──────────────────┘     └─────────────────────┘
        │                         │                         │
   reset_and_seed.py              │                    obt_sales
   generate_incremental_sales.py  │                    kpi_price_performance
   generate_anomaly_scenarios.py  │                    kpi_promo_performance
                                  │                         │
                                  │                         ▼
                           ┌──────▼──────┐          ┌──────────────┐
                           │  FastAPI    │          │  Frontend    │
                           │  (Backend)  │◀─────────│  (Django)    │
                           └─────────────┘          └──────────────┘
```

---

## 2. Ingestion Flow (data → pct_core)

> The earlier `data/generation/` pipeline (CSV generation + separate load step) has been
> removed — it was dead code, superseded by the scripts below, which write directly to
> `pct_core` via SQL. See `COMMANDES.md` for the full command reference.

### Step 1: Full Reset & Seed

**Script**: `data/scripts/reset_and_seed.py`

One-shot, destructive (truncates all core tables first). Seeds `pct_core` end to end:
countries, stores, product families/products/images, standard and store prices, promotions,
initial sales history (2025-01-01 → yesterday) with seasonal patterns, and anomaly
calibration scenarios.

### Step 2: Incremental Sales

**Script**: `data/scripts/generate_incremental_sales.py`

Idempotent — generates sales from the day after the latest existing transaction up to
yesterday. Safe to re-run on a schedule to keep `pct_core.sales_transaction` current.

### Step 3: Anomaly Calibration Scenarios (optional, standalone)

**Script**: `data/scripts/generate_anomaly_scenarios.py`

Also invoked as the last step of `reset_and_seed.py`; can be re-run independently to
regenerate calibrated anomaly scenarios (`CALIB_*` promotions) without a full reset.

---

## 3. Transformation Flow (pct_core → pct_analytics via dbt)

### dbt Pipeline

```
pct_core (source)
    │
    ▼
STAGING (renaming, typing)
    stg_sales, stg_product, stg_product_family,
    stg_store, stg_country, stg_price, stg_promotion
    │
    ▼
INTERMEDIATE (enrichment, joins)
    int_sales_enriched
    │
    ▼
MARTS (aggregation, KPI)
    obt_sales              → Full denormalized table
    kpi_price_performance  → Rolling 30d KPI + country benchmark
    kpi_promo_performance  → Product uplift (before vs during promo) + family effect
```

### Transformation Details

| Layer | Model | Transformation |
|---|---|---|
| Staging | `stg_*` | Column selection, renaming, typing |
| Intermediate | `int_sales_enriched` | Join sales × product × store × price × promotion. Compute `price_difference`, `price_difference_rate`, boolean flags |
| Mart | `obt_sales` | Add families, countries, promotion temporal classification |
| Mart | `kpi_price_performance` | 30d periodization, aggregation by (country, store, product), country benchmark, business flags |
| Mart | `kpi_promo_performance` | Product uplift (before vs during promo), family effect (cannibalization / halo), business flags |

---

## 4. Consumption Flow (pct_analytics → API → Frontend)

### Backend (FastAPI)

The API exposes `pct_core` data via REST endpoints:
- `GET /products` — Product catalog
- `GET /prices` — Standard and promotional prices
- `GET /promotions` — Active and historical promotions

#### Analytical Layer

The API also exposes `pct_analytics` data via dedicated endpoints:
- `GET /sales` — Filterable listing of sales transactions (`pct_core.sales_transaction`)
- `GET /kpis` — Aggregated KPIs computed dynamically from `pct_analytics.obt_sales`
- `GET /anomalies` — Rule-based business anomaly detection from `pct_analytics.obt_sales`
- `GET /analytics/sales` — Enriched OBT rows directly from `pct_analytics.obt_sales` with filters (product, store, country, is_promo, limit)
- `GET /analytics/sales/summary` — Aggregated KPIs per product from `pct_analytics.obt_sales` (transaction count, total revenue, avg selling price, promo share, period)

```
pct_analytics.obt_sales
        │
        ├──▶ GET /kpis                    → total_revenue, promo_share, AOV
        ├──▶ GET /anomalies               → underperforming promotions (LOW_PROMOTION_REVENUE)
        ├──▶ GET /analytics/sales         → enriched OBT rows (filterable)
        └──▶ GET /analytics/sales/summary → per-product aggregated KPIs
```

**Business logic implemented in services:**

| Service | Role |
|---|---|
| `kpi_service.py` | Dynamic KPI computation (count, sum, avg) with optional filters |
| `anomaly_service.py` | Rule-based detection: promotions with revenue < configurable threshold (fixed at 500 € — see backlog for improvement) |
| `routes/analytics_sales.py` | Raw SQL on `pct_analytics.obt_sales` — enriched rows + per-product summary |

### Frontend (Django)

Consumes the REST API to display:
- Dashboard (KPI cards, charts)
- Product catalog with per-product analytics sidebar (prices + KPIs from `obt_sales`)
- Price and promotion listings
- Anomalies as interactive cards with detail panel and actions
- **Ventes Analytiques** (`/analytique/ventes/`) — filterable table from `pct_analytics.obt_sales`

```
Django View              FastAPI endpoint           pct_analytics table
─────────────────────────────────────────────────────────────────────
AnalyticsSalesView   →   GET /analytics/sales    →  obt_sales
ProductAnalyticsView →   GET /analytics/sales/   →  obt_sales
                             summary?product_id=X
AnomaliesView        →   GET /anomalies          →  obt_sales
DashboardView        →   GET /kpis               →  obt_sales
```

---

## 5. Flow Dependencies

| Step | Prerequisites |
|---|---|
| Reset & seed | PostgreSQL running, `pct_core` schema migrated |
| Incremental sales | Reset & seed already run at least once |
| dbt run | Data present in `pct_core`, `pct_analytics` schema created |
| API | PostgreSQL accessible |
| Frontend | API accessible |

---

## 6. Execution Commands

See `COMMANDES.md` for the full, up-to-date command reference. Summary:

```bash
# 1. Start PostgreSQL
docker compose up -d postgres

# 2. Apply database migrations
cd backend && uv run alembic upgrade head && cd ..

# 3. Full reset & seed (destructive — truncates pct_core first)
DATABASE_URL="postgresql+psycopg://pct_user:pct_password@localhost:5432/pct" \
uv run python data/scripts/reset_and_seed.py

# 4. Keep sales current (idempotent, safe to re-run)
DATABASE_URL="postgresql+psycopg://pct_user:pct_password@localhost:5432/pct" \
uv run python data/scripts/generate_incremental_sales.py

# 5. Run dbt transformations
cd data && uv run dbt run --project-dir dbt && cd ..

# 6. Start the API
cd backend && uv run uvicorn app.main:app --reload
```
