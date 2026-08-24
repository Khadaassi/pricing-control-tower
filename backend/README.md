# Pricing Control Tower — Backend

_Last verified: 2026-08-24_

FastAPI REST API for the Pricing Control Tower: transactional pricing data (`pct_core` schema), RBAC, price change request workflow, and read access to the dbt-managed analytical schema (`pct_analytics`).

## Tech stack

From `backend/pyproject.toml` (Python `>=3.12,<3.13`):

- **FastAPI** — REST API framework
- **SQLAlchemy 2.x** — ORM
- **Alembic** — schema migrations (`pct_core`)
- **psycopg[binary]** — PostgreSQL driver
- **Pydantic** (via FastAPI) — request/response schemas
- **PyJWT** — internal service token verification (`app/core/internal_auth.py`)
- **prometheus-client** — `/metrics` endpoint
- **dbt-core / dbt-postgres** — also declared here as a dependency (used by `data/dbt/`, run against this backend's database)
- Dev: `pytest`, `httpx`, `ruff`

## Project structure

```text
backend/
├── app/
│   ├── main.py               # FastAPI app factory
│   ├── config.py
│   ├── db.py                 # SQLAlchemy engine/session
│   ├── api/
│   │   ├── router.py
│   │   ├── dependencies/current_user.py
│   │   └── routes/            # analytics_sales, anomalies, countries, kpis, me,
│   │                           #   metrics, price_change_requests, price_history,
│   │                           #   prices, product_families, products, promotions,
│   │                           #   sales, stores, technical
│   ├── core/                  # internal_auth.py, logging_config.py, metrics.py
│   ├── middleware/            # logging_middleware.py, metrics_middleware.py
│   ├── models/                 # SQLAlchemy models: country, store, product,
│   │                           #   product_family, product_image, price, price_history,
│   │                           #   promotion, sales_transaction, user_account, role,
│   │                           #   role_permission, user_role, permission,
│   │                           #   price_change_request, audit_log, obt_sales,
│   │                           #   kpi_promo_performance
│   ├── schemas/                # Pydantic schemas mirroring the models above
│   └── services/                # anomaly_service, kpi_service, price_history_service,
│                                #   price_change_request_service, rbac_service, scope_service
├── alembic/
│   ├── env.py
│   └── versions/                # 22 migrations (init, per-table creation, RBAC tables,
│                                 #   price change request constraints, etc.)
├── scripts/                     # create_schemas.py, seed_rbac_roles_permissions.py,
│                                 #   seed_business_demo_users.py, manual_validate_price_workflow.sh
├── tests/                        # see backend/tests/README.md
├── alembic.ini
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

## RBAC

The backend enforces role-based access control:

- Models: `app/models/role.py`, `role_permission.py`, `user_role.py`, `permission.py`, plus RBAC fields on `user_account.py`.
- Services: `app/services/rbac_service.py` (permission checks), `app/services/scope_service.py` (country/store scoping).
- Identity: the caller's identity is passed via `X-User-Email`, or via a signed internal service token (`app/core/internal_auth.py`) when the frontend or `ai_service` call on a user's behalf — the shared secret is `INTERNAL_AUTH_SECRET`.
- Seed data: `scripts/seed_rbac_roles_permissions.py` seeds roles/permissions; `scripts/seed_business_demo_users.py` seeds demo accounts.
- Tests: `tests/test_rbac_permissions.py`, `tests/test_scope_enforcement.py`.

## Database migrations (Alembic)

`backend/alembic/versions/` currently contains 22 migrations managing the `pct_core` schema: initial tables (country, store, product, product_family, product_image, price, promotion, sales_transaction, user_account, price_history, price_change_request, audit_log), RBAC tables (`role`, `permission`, `role_permission`, `user_role`), and constraint/business-rule refinements.

```bash
uv run alembic upgrade head
```

## Run locally

```bash
uv sync --all-groups
cp .env.example .env   # fill in POSTGRES_* / DATABASE_URL / INTERNAL_AUTH_SECRET
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

## Tests

```bash
uv run pytest
```

See [tests/README.md](tests/README.md) for the actual list of test files.

## Lint

```bash
uv run ruff check app tests
```