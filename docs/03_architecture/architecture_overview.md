# Architecture Overview — Pricing Control Tower

## 1. Overview

The Pricing Control Tower project is organized in independent layers communicating via well-defined interfaces:

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Django)                  │
│              Tailwind CSS — SSR — Pages              │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / REST
┌──────────────────────▼──────────────────────────────┐
│                  Backend (FastAPI)                   │
│       API REST — SQLAlchemy — Alembic migrations    │
└──────────────────────┬──────────────────────────────┘
                       │ SQL
┌──────────────────────▼──────────────────────────────┐
│               PostgreSQL 16 (Docker)                 │
│                                                     │
│  ┌─────────────┐          ┌──────────────────┐     │
│  │  pct_core   │          │  pct_analytics   │     │
│  │ (transac.)  │──dbt────▶│ (analytical views)│    │
│  └─────────────┘          └──────────────────┘     │
└─────────────────────────────────────────────────────┘
```

---

## 2. Components

| Component | Technology | Role |
|---|---|---|
| **Backend** | FastAPI + SQLAlchemy | REST API, business logic, transactional data access |
| **Frontend** | Django + Tailwind CSS | User interface, server-side rendering (SSR) |
| **Database** | PostgreSQL 16 | Transactional (`pct_core`) and analytical (`pct_analytics`) storage |
| **Transformation** | dbt (dbt-postgres) | Transformation pipeline: staging → intermediate → marts |
| **Data Generation** | Python (scripts) | Realistic sales simulation for MVP |
| **Containerization** | Docker Compose | Local orchestration (PostgreSQL) |

---

## 3. Database Schemas

### `pct_core` — Transactional Data

Managed by Alembic (versioned migrations). Contains:

- `country`, `store` — Geographic reference
- `product_family`, `product`, `product_image` — Product reference
- `price` — Prices (standard and promotional)
- `promotion` — Promotions
- `sales_transaction` — Sales transactions
- `user_account` — Users

### `pct_analytics` — Analytical Data

Managed by dbt. Contains materialized views:

- **Staging**: `stg_sales`, `stg_product`, `stg_store`, `stg_country`, `stg_price`, `stg_promotion`, `stg_product_family`
- **Intermediate**: `int_sales_enriched`
- **Marts**: `obt_sales`, `kpi_price_performance`, `kpi_promo_performance`

---

## 4. Code Organization

```
princing-control-tower/
├── backend/              # FastAPI API + Alembic migrations
│   ├── app/              # Application code (routes, models, schemas)
│   ├── alembic/          # pct_core schema migrations
│   ├── tests/            # Unit and integration tests
│   └── docker-compose.yml
├── data/                 # Data layer
│   ├── dbt/              # dbt project (staging, intermediate, marts)
│   ├── generated/        # Generated CSV files
│   └── generation/       # Data generation scripts
├── docs/                 # Full documentation
│   ├── 01_functional/    # Functional specification
│   ├── 02_data_model/    # CDM, LDM, PDM
│   ├── 03_architecture/  # Architecture, flows, technical choices
│   ├── 04_agilite/       # Backlog, epics, user stories
│   └── 05_runbook/       # Installation, deployment, monitoring
└── frontend/             # Django application (upcoming)
```

---

## 5. Inter-component Communication

| Source | Destination | Protocol | Description |
|---|---|---|---|
| Frontend | Backend | HTTP REST | API endpoint consumption |
| Backend | PostgreSQL | SQL (asyncpg) | CRUD on `pct_core` |
| dbt | PostgreSQL | SQL | Read `pct_core`, write `pct_analytics` |
| Generation scripts | PostgreSQL | SQL (psycopg2) | Simulated data insertion |

---

## 6. Architecture Principles

- **Separation of concerns**: each component has a single role
- **Read-only analytical layer**: dbt never modifies `pct_core`
- **Reproducible simulated data**: fixed seed for generation
- **Versioned migrations**: Alembic for all schema changes
- **Stateless API**: no server-side sessions
