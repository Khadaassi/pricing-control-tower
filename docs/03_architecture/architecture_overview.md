# Architecture Overview — Pricing Control Tower

## 1. Overview

The Pricing Control Tower project is organized in independent layers communicating via well-defined interfaces:

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Django)                  │
│              Tailwind CSS — SSR — Pages              │
└──────────────┬──────────────────────────────────────┘
               │ HTTP / REST          │ HTTP / REST
               │                     │ (chatbot)
┌──────────────▼───────┐   ┌─────────▼───────────────┐
│   Backend (FastAPI)  │   │   AI Service (FastAPI)   │
│  API REST — SQLAlch. │   │  Chatbot — Tool routing  │
│  Alembic migrations  │◄──┤  Groq LLM (llama-3.1)   │
└──────────┬───────────┘   └─────────────────────────┘
           │ SQL
┌──────────▼───────────────────────────────────────────┐
│                  PostgreSQL 16 (Docker)               │
│  ┌─────────────┐          ┌──────────────────┐       │
│  │  pct_core   │          │  pct_analytics   │       │
│  │ (transac.)  │──dbt────▶│ (analytical views)│      │
│  └─────────────┘          └──────────────────┘       │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│                  Monitoring Stack                     │
│  Prometheus ←── scrapes /metrics on all services     │
│  Grafana    ←── reads Prometheus, displays dashboard │
│  cAdvisor   ←── scrapes Docker container metrics     │
└──────────────────────────────────────────────────────┘
```

---

## 2. Components

| Component        | Technology                  | Role |
| ---------------- | --------------------------- | ---- |
| **Backend**      | FastAPI + SQLAlchemy        | REST API, business logic, transactional data access |
| **Frontend**     | Django + Tailwind CSS       | User interface, server-side rendering (SSR), chatbot UI |
| **AI Service**   | FastAPI + Groq (llama-3.1)  | Chatbot orchestration, intent routing, backend-dependent tool execution |
| **Database**     | PostgreSQL 16               | Transactional (`pct_core`) and analytical (`pct_analytics`) storage |
| **Transformation** | dbt (dbt-postgres)        | Transformation pipeline: staging → intermediate → marts |
| **Data Generation** | Python (scripts)         | Realistic sales simulation for MVP |
| **Containerization** | Docker Compose          | Full stack orchestration (all services) |
| **Prometheus**   | prom/prometheus             | Metrics collection — scrapes `/metrics` on backend, frontend, ai_service, cAdvisor |
| **Grafana**      | grafana/grafana             | Metrics visualization — global observability dashboard |
| **cAdvisor**     | gcr.io/cadvisor             | Container-level CPU, memory and I/O metrics |

---

## 3. Database Schemas

### `pct_core` — Transactional Data

Managed by Alembic (versioned migrations). Contains:

- `country`, `store` — Geographic reference
- `product_family`, `product`, `product_image` — Product reference
- `price` — Prices (standard and promotional)
- `promotion` — Promotions
- `sales_transaction` — Sales transactions
- `user_account`, `permission`, `audit_log` — RBAC and audit trail

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
│   ├── app/              # Application code (routes, models, schemas, metrics)
│   ├── alembic/          # pct_core schema migrations
│   └── tests/            # Unit and integration tests
├── ai_service/           # FastAPI AI chatbot service
│   ├── app/              # Chatbot orchestrator, tools, routes, metrics
│   └── tests/            # AI service tests
├── frontend/             # Django application
│   ├── core/             # Views, models, API client, health, metrics
│   └── theme/            # Tailwind CSS configuration
├── monitoring/           # Observability configuration
│   ├── prometheus/       # prometheus.yml scrape configuration
│   └── grafana/          # Dashboard provisioning (JSON)
├── data/                 # Data layer
│   ├── dbt/              # dbt project (staging, intermediate, marts)
│   ├── generated/        # Generated CSV files
│   └── generation/       # Data generation scripts
├── backups/              # Local database backups (dumps excluded from git)
│   └── postgres/
├── docs/                 # Full documentation
│   ├── 01_functional/    # Functional specification and use cases
│   ├── 02_data_model/    # CDM, LDM, PDM
│   ├── 03_architecture/  # Architecture, flows, technical choices
│   ├── 04_agilite/       # Backlog, epics, user stories
│   ├── 05_runbook/       # CI/CD, deployment, quality gates
│   ├── 06_validation/    # Validation reports and incident documentation
│   └── 07_operations/    # Operations and maintenance runbooks
└── docker-compose.yml    # Full stack orchestration
```

---

## 5. Inter-component Communication

| Source       | Destination  | Protocol       | Description |
| ------------ | ------------ | -------------- | ----------- |
| Frontend     | Backend      | HTTP REST      | API endpoint consumption (products, prices, KPIs, anomalies, workflow) |
| Frontend     | AI Service   | HTTP REST      | Chatbot requests (`POST /chat`) |
| AI Service   | Backend      | HTTP REST      | Tool execution — backend-dependent queries (KPIs, anomalies, price change requests) |
| AI Service   | Groq API     | HTTPS          | LLM inference (llama-3.1-8b-instant) |
| Backend      | PostgreSQL   | SQL (asyncpg)  | CRUD on `pct_core` |
| dbt          | PostgreSQL   | SQL            | Read `pct_core`, write `pct_analytics` |
| Generation scripts | PostgreSQL | SQL (psycopg2) | Simulated data insertion |
| Prometheus   | Backend      | HTTP scrape    | `/metrics` endpoint — FastAPI application metrics |
| Prometheus   | Frontend     | HTTP scrape    | `/metrics` endpoint — Django application metrics |
| Prometheus   | AI Service   | HTTP scrape    | `/metrics` endpoint — chatbot metrics |
| Prometheus   | cAdvisor     | HTTP scrape    | Container-level resource metrics |
| Grafana      | Prometheus   | PromQL HTTP    | Dashboard data queries |

---

## 6. Service URLs (local Docker Compose)

| Service    | Local URL                |
| ---------- | ------------------------ |
| Backend    | `http://localhost:8000`  |
| Frontend   | `http://localhost:8001`  |
| AI Service | `http://localhost:8002`  |
| Prometheus | `http://localhost:9090`  |
| Grafana    | `http://localhost:3000`  |
| cAdvisor   | `http://localhost:8080`  |

---

## 7. Architecture Principles

- **Separation of concerns**: each component has a single, well-defined role
- **Read-only analytical layer**: dbt never modifies `pct_core`
- **Reproducible simulated data**: fixed seed for generation
- **Versioned migrations**: Alembic for all schema changes
- **Stateless API**: no server-side sessions; identity forwarded via `X-User-Email` header
- **Observability by design**: structured JSON logs, Prometheus metrics and `/health` endpoints on all application services
- **Graceful degradation**: frontend and AI service absorb backend failures and return meaningful errors rather than HTTP 500
