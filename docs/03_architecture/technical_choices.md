# Technical Choices — Pricing Control Tower

## 1. Backend

| Technology | Version | Justification |
|---|---|---|
| **Python** | 3.11+ | Primary language — mature data and AI ecosystem |
| **FastAPI** | 0.100+ | Modern API framework, native typing, auto documentation (OpenAPI) |
| **SQLAlchemy** | 2.x | Robust ORM, async support, declarative mapping |
| **Alembic** | 1.x | Versioned migrations, native SQLAlchemy integration |
| **uv** | — | Fast package manager, pip replacement |
| **Pydantic** | 2.x | Data validation, serialization, API schemas |

---

## 2. Database

| Technology | Version | Justification |
|---|---|---|
| **PostgreSQL** | 16 | High-performance relational DBMS, JSON support, CTEs, window functions |
| **Docker Compose** | — | Simple and reproducible local orchestration |

### Schema Organization

| Schema | Role | Management |
|---|---|---|
| `pct_core` | Transactional data and reference | Alembic (migrations) |
| `pct_analytics` | Analytical views and KPIs | dbt (transformations) |

---

## 3. Data / Analytics

| Technology | Version | Justification |
|---|---|---|
| **dbt** (dbt-core + dbt-postgres) | 1.8+ | Versioned SQL transformation, built-in tests, auto documentation |
| **Python (scripts)** | — | Reproducible simulated data generation |

### dbt Architecture

- **Staging**: extraction and renaming from `pct_core` sources
- **Intermediate**: enrichment via joins (sales × dimensions)
- **Marts**: denormalized tables (`obt_sales`) and KPIs (`kpi_price_performance`, `kpi_promo_performance`)

### Analytical Modeling Choices

- **OBT (One Big Table)**: denormalized approach suited to MVP volume (~20k rows)
- **Rolling periodization**: 30-day vs previous 30-day comparison (no fiscal calendar)
- **Country benchmark**: volume-weighted average price at country × product level

---

## 4. Frontend

| Technology | Justification |
|---|---|
| **Django** | Full-stack Python framework, server-side rendering (SSR), built-in admin |
| **Tailwind CSS** | Utility-first CSS, rapid development, responsive design |

### UI Language

The application UI is entirely in **French**. This choice stems directly from the product data: products are scraped from a French-speaking e-commerce site (Fitness Boutique), and their names, families and descriptions are in French. Using an English UI would create a visual inconsistency between UI labels and displayed data.

Translation scope:
- Django templates (labels, titles, error/success messages, empty states, buttons)
- Navigation sidebar (`base.html`) and mobile nav bar
- Context strings in `views.py` (KPI labels, scopes, statuses)
- No dependency on Django's `i18n` system — translations are hardcoded directly (MVP)

---

## 5. Infrastructure

| Technology | Justification |
|---|---|
| **Docker** | Containerization for reproducibility |
| **Docker Compose** | Local orchestration (PostgreSQL) |
| **GCP Cloud Run** (target) | Serverless cloud deployment |

> ⚠️ **Obsolete (verified 2026-08-24)** — the actual GCP deployment does not use Cloud Run. The Terraform infrastructure (`infra/terraform/*.tf`) provisions a Compute Engine VM (`google_compute_instance`) running the stack via Docker Compose (`infra/compose/docker-compose.gcp.yml`), with Cloud SQL (`google_sql_database_instance`) for PostgreSQL and Secret Manager for secrets. See [gcp_cloud_architecture.md](gcp_cloud_architecture.md) for the up-to-date detail.

---

## 6. Quality and Testing

| Tool | Role |
|---|---|
| **pytest** | Backend unit and integration tests |
| **dbt test** | Data tests (not_null, unique, accepted_values) |
| **GitHub Actions** (target) | Automated CI/CD |

> ⚠️ **Obsolete (verified 2026-08-24)** — no longer just a target: `.github/workflows/ci.yml` exists and actually runs tests, lint, Tailwind CSS build, and Docker image builds (backend, frontend, ai_service).

---

## 7. Key Decisions

| Decision | Reason |
|---|---|
| Single PostgreSQL (core + analytics) | MVP simplicity, no separate data warehouse needed |
| dbt as views (no materialized tables) | Low volume, instant refresh |
| Python generation rather than Faker | Full control over distribution and reproducibility (fixed seed) |
| Stateless API | Scalability, simplicity, no session management |
| backend/data/frontend separation | Deployment independence, clear responsibilities |
| French UI language | Consistency with French product data scraped from Fitness Boutique |
| Direct translation without Django i18n | MVP simplicity — single target language, no multilingual requirement |
