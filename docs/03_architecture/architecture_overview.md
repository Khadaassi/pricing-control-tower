# Architecture Overview — Pricing Control Tower

_Last verified: 2026-08-24_

> ⚠️ **Obsolete (verified 2026-08-24)** — `schema-architecture-v0.png` (dated 5 May) is a generic conceptual diagram (Airflow/OpenWeatherMap-style icons not representative of the actual project) that shows neither the RAG chatbot, nor the detailed RBAC, nor the monitoring stack (Prometheus/Grafana/cAdvisor), nor the actual GCP deployment (Compute Engine + Cloud SQL + Secret Manager via Terraform). Current state: see the ASCII diagram below (itself incomplete, see associated note) and the sections added further down in this document. A v1 diagram is being prepared separately (out of scope for this verification pass).

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

> ⚠️ **Obsolete (verified 2026-08-24)** — this ASCII diagram does not represent the chatbot's RAG components (ChromaDB for vector storage, Ollama for embeddings — only Groq/llama-3.1 for generation appears), nor the GCP deployment (Compute Engine + Cloud SQL + Secret Manager). Current state: see §2 (Components), §5 (Inter-component Communication) and §8 (Cloud Deployment) below, as well as `ai_chatbot_hybrid_rag_architecture.md` and `gcp_cloud_architecture.md`.

---

## 2. Components

| Component        | Technology                  | Role |
| ---------------- | --------------------------- | ---- |
| **Backend**      | FastAPI + SQLAlchemy        | REST API, business logic, transactional data access |
| **Frontend**     | Django + Tailwind CSS       | User interface, server-side rendering (SSR), chatbot UI |
| **AI Service**   | FastAPI + Groq (llama-3.1)  | Chatbot orchestration, intent routing, backend-dependent tool execution |
| **ChromaDB**     | chromadb/chroma (vector store) | RAG document store for the chatbot's documentary knowledge — see `ai_chatbot_hybrid_rag_architecture.md` |
| **Ollama**       | ollama/ollama                | Local embedding generation for RAG (`OllamaEmbeddingProvider`) — see `ai_chatbot_hybrid_rag_architecture.md` |
| **Database**     | PostgreSQL 16               | Transactional (`pct_core`) and analytical (`pct_analytics`) storage |
| **Transformation** | dbt (dbt-postgres)        | Transformation pipeline: staging → intermediate → marts |
| **Data Generation** | Python (scripts)         | Realistic sales simulation for MVP |
| **Containerization** | Docker Compose          | Full stack orchestration (all services) |
| **Prometheus**   | prom/prometheus             | Metrics collection — scrapes `/metrics` on backend, frontend, ai_service, cAdvisor |
| **Grafana**      | grafana/grafana             | Metrics visualization — global observability dashboard |
| **cAdvisor**     | gcr.io/cadvisor             | Container-level CPU, memory and I/O metrics |

> ⚠️ **Obsolete (verified 2026-08-24)** — the "AI Service" row above only mentions Groq and under-represents the chatbot's actual architecture. Current state: the chatbot combines Tool Calling (live business data via the backend), hybrid RAG (ChromaDB + Ollama for document search — see ChromaDB/Ollama rows above) and LLM generation (Groq/llama-3.1). Full detail in `ai_chatbot_hybrid_rag_architecture.md`.

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

> ⚠️ **Obsolete (verified 2026-08-24)** — this list does not mention the `role`, `user_role` and `role_permission` tables. Current state: RBAC is a complete `user → role → permission` model (`backend/app/models/role.py`, `user_role.py`, `role_permission.py`, `permission.py`), with verification logic centralized in `backend/app/services/rbac_service.py`. Full detail in `authentication_rbac_architecture.md`.

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
├── infra/                # GCP deployment (Sprint 14)
│   ├── terraform/        # IaC — Compute Engine, Cloud SQL, Secret Manager, network, IAM
│   └── compose/          # docker-compose.gcp.yml + secret-fetching script for the VM
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
| AI Service   | ChromaDB     | HTTP REST      | RAG vector search — documentary knowledge retrieval |
| AI Service   | Ollama       | HTTP REST      | Embedding generation for RAG queries |
| rag_bootstrap | ChromaDB / Ollama | HTTP REST | One-off corpus ingestion at stack startup (`ai_service/scripts/bootstrap_rag.py`) |
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
| ChromaDB   | `http://localhost:8010`  |
| Ollama     | `http://localhost:11434` |
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

---

## 8. Cloud Deployment (GCP)

_Section absent from the previous version of this document — added 2026-08-24, verified against `infra/terraform/` and `infra/compose/`._

Since Sprint 14, the stack can be deployed to Google Cloud Platform:

- **Provisioning (Terraform, `infra/terraform/`)**: `google_compute_instance` (VM running Docker Compose), `google_sql_database_instance` (managed Cloud SQL, replacing the containerized `postgres` service used locally), `google_secret_manager_secret*` (DB password, `INTERNAL_AUTH_SECRET`, Django secret key, Groq API key, Grafana admin password, shared demo account password), plus the associated network, firewall and IAM resources.
- **Application deployment**: `infra/compose/docker-compose.gcp.yml` + `infra/compose/fetch-secrets.sh` run on the VM.
- Full architecture, diagram and choice justifications: `gcp_cloud_architecture.md`. Operations runbook: `docs/07_operations/gcp_exploitation_runbook.md`.
