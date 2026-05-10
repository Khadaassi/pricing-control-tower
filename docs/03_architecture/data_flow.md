# Data Flow — Pricing Control Tower

## 1. Data Flow Overview

```
┌───────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Python Scripts   │────▶│   pct_core       │────▶│   pct_analytics     │
│  (generation)     │     │   (PostgreSQL)   │     │   (dbt views)       │
└───────────────────┘     └──────────────────┘     └─────────────────────┘
        │                         │                         │
   seed_reference_data.py         │                    obt_sales
   generate_sales_dataset.py      │                    kpi_price_performance
   load_sales_transactions.py     │                    kpi_promo_performance
                                  │                         │
                                  │                         ▼
                           ┌──────▼──────┐          ┌──────────────┐
                           │  FastAPI    │          │  Frontend    │
                           │  (Backend)  │◀─────────│  (Django)    │
                           └─────────────┘          └──────────────┘
```

---

## 2. Ingestion Flow (data → pct_core)

### Step 1: Reference Data Seeding

**Script**: `data/generation/seed_reference_data.py`

Inserts reference data into `pct_core`:
- Countries (country)
- Stores (store)
- Product families (product_family)
- Products (product)
- Standard and promotional prices (price)
- Promotions (promotion)

### Step 2: Sales Dataset Generation

**Script**: `data/generation/generate_sales_dataset.py`

Generates a CSV file (`data/generated/sales_transactions.csv`) containing ~20,000 simulated transactions over 6 months.

Generation rules:
- Non-uniform quantity distribution (product + store variability + promo effect)
- Simple seasonality
- Consistency with active prices and promotions at each date

### Step 3: Database Loading

**Script**: `data/generation/load_sales_transactions.py`

Loads the CSV into the `pct_core.sales_transaction` table.

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
| Reference data seed | PostgreSQL running, `pct_core` schema created |
| Sales generation | Reference data inserted (products, stores, prices, promos) |
| Sales loading | CSV generated |
| dbt run | Data present in `pct_core`, `pct_analytics` schema created |
| API | PostgreSQL accessible |
| Frontend | API accessible |

---

## 6. Execution Commands

```bash
# 1. Start PostgreSQL
cd backend
docker compose up -d

# 2. Apply database migrations
alembic upgrade head

# 3. Return to repository root
cd ..

# 4. Seed reference data
python data/generation/seed_reference_data.py

# 5. Generate sales transactions
python data/generation/generate_sales_dataset.py

# 6. Load sales transactions into PostgreSQL
python data/generation/load_sales_transactions.py

# 7. Run dbt transformations
cd data/dbt
dbt run

# 8. Start the API
cd ../../backend
uvicorn app.main:app --reload
```
