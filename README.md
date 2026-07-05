# Pricing Control Tower

A web application for centralized price management, analytics, and governance across a multi-store organization. Built as part of an RNCP professional certification in AI development.

---

## Overview

The Pricing Control Tower provides business users with tools to:

- **Analyze** sales performance in quantity and revenue across stores and nationally
- **Manage prices and promotions** — consult, compare, and track full price history
- **Govern pricing decisions** — manage price change request workflows with a full audit trail
- **Detect anomalies** — identify pricing inconsistencies and performance outliers
- **Chat with an AI assistant** — ask natural language questions about KPIs, anomalies, and corrective actions (powered by Groq / llama-3.1)

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Django)                 │
│              Tailwind CSS — SSR — Pages             │
└──────────────┬──────────────────────────────────────┘
               │ HTTP / REST         │ HTTP / REST
               │                     │ (chatbot)
┌──────────────▼───────┐   ┌─────────▼───────────────┐
│   Backend (FastAPI)  │   │   AI Service (FastAPI)  │
│  REST API — SQLAlch. │   │  Chatbot — Tool routing │
│  Alembic migrations  │◄──┤  Groq LLM (llama-3.1)   │
└──────────┬───────────┘   └─────────────────────────┘
           │ SQL
┌──────────▼───────────────────────────────────────────┐
│                  PostgreSQL 16 (Docker)              │
│  ┌─────────────┐          ┌──────────────────┐       │
│  │  pct_core   │          │  pct_analytics   │       │
│  │ (transac.)  │──dbt────▶│(analytical views)│       │
│  └─────────────┘          └──────────────────┘       │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│                  Monitoring Stack                    │
│  Prometheus ←── scrapes /metrics on all services     │
│  Grafana    ←── reads Prometheus, displays dashboard │
│  cAdvisor   ←── scrapes Docker container metrics     │
└──────────────────────────────────────────────────────┘
```

| Component | Technology | Role |
|---|---|---|
| **Backend** | FastAPI + SQLAlchemy + Alembic | REST API, business logic, transactional data |
| **Frontend** | Django + Tailwind CSS | Server-side rendered UI, chatbot interface |
| **AI Service** | FastAPI + Groq (llama-3.1) | Chatbot orchestration, intent routing, tool execution |
| **Database** | PostgreSQL 16 | `pct_core` (transactional) + `pct_analytics` (analytical) |
| **Transformation** | dbt (dbt-postgres) | Staging → intermediate → marts pipeline |
| **Monitoring** | Prometheus + Grafana + cAdvisor | Metrics collection and observability dashboard |
| **Containerization** | Docker Compose | Full stack orchestration |

---

## Tech Stack

**Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic 2.x, uv

**Frontend:** Python / Django, Tailwind CSS (SSR, no JavaScript framework)

**Data:** PostgreSQL 16, dbt-core 1.8+, custom Python data generation scripts

**AI:** Groq API (llama-3.1-8b-instant), tool-based agent pattern

**Infra:** Docker, Docker Compose, GitHub Actions CI, GCP Cloud Run (target deployment)

---

## Project Structure

```
princing-control-tower/
├── backend/              # FastAPI API + Alembic migrations
│   ├── app/              # Routes, models, schemas, metrics, middleware
│   ├── alembic/          # pct_core schema versioned migrations
│   └── tests/            # Unit and integration tests
├── ai_service/           # FastAPI AI chatbot service
│   ├── app/              # Chatbot orchestrator, tools, routes, metrics
│   └── tests/            # AI service tests
├── frontend/             # Django application
│   ├── core/             # Views, models, API client, health, metrics
│   └── theme/            # Tailwind CSS configuration
├── monitoring/           # Observability configuration
│   ├── prometheus/       # prometheus.yml scrape config
│   └── grafana/          # Dashboard provisioning (JSON)
├── data/                 # Data layer
│   ├── dbt/              # dbt project (staging, intermediate, marts)
│   ├── generated/        # Generated CSV files
│   └── generation/       # Data generation scripts
├── docs/                 # Architecture, functional specs, runbooks
└── docker-compose.yml    # Full stack orchestration
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- [uv](https://github.com/astral-sh/uv) (Python package manager)

### Run the full stack

```bash
git clone <repo_url>
cd princing-control-tower
docker compose up -d --build
```

Services will be available at:

| Service | URL |
|---|---|
| Frontend (Django) | http://localhost:8001 |
| Backend API (FastAPI) | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| AI Service | http://localhost:8002 |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |

### Run locally (host-based development)

See [docs/05_runbook/run_local.md](docs/05_runbook/run_local.md) for the full step-by-step guide covering environment setup, migrations, data generation, and dbt transformations.

---

## Database Schemas

### `pct_core` — Transactional (Alembic-managed)

`country`, `store`, `product_family`, `product`, `product_image`, `price`, `promotion`, `sales_transaction`, `user_account`, `permission`, `audit_log`

### `pct_analytics` — Analytical (dbt-managed)

- **Staging**: `stg_sales`, `stg_product`, `stg_store`, `stg_country`, `stg_price`, `stg_promotion`, `stg_product_family`
- **Intermediate**: `int_sales_enriched`
- **Marts**: `obt_sales`, `kpi_price_performance`, `kpi_promo_performance`

---

## RBAC

The application uses a role-based access control model with identity passed via `X-User-Email` header. Target roles: `PRICING_ANALYST`, `STORE_MANAGER`, `STORE_DIRECTOR`, `COUNTRY_DIRECTOR`, `ADMINISTRATOR`. Permissions are scoped by country and store. See [docs/03_architecture/authentication_rbac_architecture.md](docs/03_architecture/authentication_rbac_architecture.md).

---

## Testing & Quality

```bash
# Backend tests
cd backend && pytest

# dbt data tests
cd data/dbt && dbt test
```

CI runs on GitHub Actions on every push. See [.github/workflows/ci.yml](.github/workflows/ci.yml).

---

## Documentation

| Doc | Path |
|---|---|
| Functional specification | [docs/01_functional/cahier_des_charges_fonctionnel.md](docs/01_functional/cahier_des_charges_fonctionnel.md) |
| Data models (CDM / LDM / PDM) | [docs/02_data_model/](docs/02_data_model/) |
| Architecture overview | [docs/03_architecture/architecture_overview.md](docs/03_architecture/architecture_overview.md) |
| API design | [docs/03_architecture/api_design.md](docs/03_architecture/api_design.md) |
| Technical choices | [docs/03_architecture/technical_choices.md](docs/03_architecture/technical_choices.md) |
| RBAC architecture | [docs/03_architecture/authentication_rbac_architecture.md](docs/03_architecture/authentication_rbac_architecture.md) |
| Run local guide | [docs/05_runbook/run_local.md](docs/05_runbook/run_local.md) |
| CI/CD architecture | [docs/05_runbook/ci_cd_architecture.md](docs/05_runbook/ci_cd_architecture.md) |
| Monitoring metrics | [docs/05_runbook/application_monitoring_metrics.md](docs/05_runbook/application_monitoring_metrics.md) |
