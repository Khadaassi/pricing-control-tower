# Run Local — Local Execution Guide

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- uv (Python package manager)
- Git

---

## 1. Clone the Project

```bash
git clone <repo_url>
cd princing-control-tower
```

---

## 2. Start PostgreSQL

PostgreSQL is defined in the root `docker-compose.yml` (alongside `backend`, `frontend`, `ai_service`,
`prometheus` and `grafana`). To run just the database for host-based backend development:

```bash
docker compose up -d postgres
```

To run the full containerized stack instead (no need for steps 3, 5, and the `uvicorn`/`runserver`
commands further down), use `docker compose up -d --build` from the repo root.

Verification:

```bash
docker compose exec postgres psql -U pct_user -d pct -c "SELECT 1;"
```

---

## 3. Configure the Python Environment

```bash
cd backend
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

---

## 4. Environment Variables

Create a `backend/.env` file:

```env
POSTGRES_USER=pct_user
POSTGRES_PASSWORD=pct_password
POSTGRES_DB=pct
DATABASE_URL=postgresql://pct_user:pct_password@localhost:5432/pct
```

---

## 5. Apply Migrations

```bash
cd backend
alembic upgrade head
```

This creates the `pct_core` schema and all tables (country, store, product, price, promotion, sales_transaction, etc.).

---

## 6. Full Reset & Seed

> Replaces the old `data/generation/` CSV pipeline (removed — dead code, superseded by this
> script, which writes directly to `pct_core` via SQL).

```bash
DATABASE_URL="postgresql+psycopg://pct_user:pct_password@localhost:5432/pct" \
uv run python data/scripts/reset_and_seed.py
```

Destructive (truncates all core tables first). Seeds users, countries, stores, families,
products, prices, promotions, initial sales history, and anomaly calibration scenarios.

---

## 7. Keep Sales Current

```bash
DATABASE_URL="postgresql+psycopg://pct_user:pct_password@localhost:5432/pct" \
uv run python data/scripts/generate_incremental_sales.py
```

Idempotent — generates sales from the day after the latest transaction up to yesterday.
Safe to re-run.

---

## 8. Run dbt

Le projet `data/` utilise `uv` avec Python 3.12. Lancer depuis `data/dbt/` :

```bash
cd data
uv run dbt run --select +obt_sales +kpi_price_performance +kpi_promo_performance
```

> **Note** : Le fichier `data/.python-version` doit contenir `3.12.7` et `data/pyproject.toml` doit avoir `requires-python = ">=3.12"` et `dbt-postgres>=1.8.0` dans les dépendances.

This creates views in the `pct_analytics` schema:
- `stg_*` (staging)
- `int_sales_enriched` (intermediate)
- `obt_sales` (mart — OBT)
- `kpi_price_performance` (mart — KPI)
- `kpi_promo_performance` (mart — KPI)

### dbt Tests

```bash
dbt test
```

---

## 9. Start the API

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

The API is accessible at `http://localhost:8000`.

Interactive documentation: `http://localhost:8000/docs`

---

## 10. Start the Frontend

```bash
cd frontend
uv run python manage.py runserver 8001
```

Le frontend est accessible à `http://localhost:8001`.

> Le frontend appelle le backend FastAPI sur `http://127.0.0.1:8000` (configurable via `FASTAPI_BASE_URL` dans `frontend/config/settings.py`).

---

## 11. Quick Verifications

```bash
# API health
curl http://localhost:8000/health

# Product list
curl http://localhost:8000/products

# KPIs from psql
docker compose exec postgres psql -U pct_user -d pct \
  -c "SELECT * FROM pct_analytics.kpi_price_performance LIMIT 5;"
```

---

## Command Summary

| Step | Command |
|---|---|
| PostgreSQL | `docker compose up -d postgres` |
| Migrations | `cd backend && alembic upgrade head` |
| Reset & seed | `uv run python data/scripts/reset_and_seed.py` |
| Incremental sales | `uv run python data/scripts/generate_incremental_sales.py` |
| dbt | `cd data && uv run dbt run --select +obt_sales +kpi_price_performance +kpi_promo_performance` |
| dbt tests | `cd data && uv run dbt test` |
| API | `cd backend && uvicorn app.main:app --reload --port 8000` |
| Frontend | `cd frontend && uv run python manage.py runserver 8001` |
