# FULL BACKLOG (ATOMIC)

## EPIC 1 — Project Setup & Environment

### Feature 1.1 — Repository Initialization
T1 — Create GitHub repo
T2 — Add README.md
T3 — Add Python .gitignore
T4 — Initialize git flow (main/dev branches)

### Feature 1.2 — Project Structure
T5 — Create /backend folder
T6 — Create /frontend folder
T7 — Create /data folder
T8 — Create /docs folder
T9 — Create docs subfolders (functional, data_model, architecture, agile)

### Feature 1.3 — Python Environment
T10 — Initialize uv environment
T11 — Create pyproject.toml
T12 — Install FastAPI
T13 — Install Uvicorn
T14 — Install SQLAlchemy
T15 — Install Alembic
T16 — Install psycopg2 / asyncpg


## EPIC 2 — PostgreSQL Database

### Feature 2.1 — PostgreSQL Setup
T17 — Add PostgreSQL to docker-compose
T18 — Configure DB environment variables
T19 — Verify DB connection (psql)
T20 — Create pct database

### Feature 2.2 — Schema Creation
T21 — Create pct_core schema
T22 — Create pct_analytics schema
T23 — Verify via psql

### Feature 2.3 — Alembic Setup
T24 — Initialize Alembic
T25 — Configure connection string
T26 — Test empty migration

### Feature 2.4 — Reference Tables
T27 — Create country table
T28 — Create store table
T29 — Create product_family table
T30 — Create product table
T31 — Create product_image table

### Feature 2.5 — User & Audit Tables
T32 — Create app_user table
T33 — Create audit_log table

### Feature 2.6 — Pricing Tables
T34 — Create promotion table
T35 — Create price table
T36 — Add CHECK constraints for price_scope
T37 — Add CHECK constraints for price_type
T38 — Add promo ↔ price_type constraint

### Feature 2.7 — Pricing Workflow
T39 — Create price_change_request table
T40 — Add scope column
T41 — Add FK approved_price_id

### Feature 2.8 — History
T42 — Create price_history table

### Feature 2.9 — Transactions
T43 — Create sales_transaction table
T44 — Add CHECK constraints for quantity
T45 — Add CHECK constraints for price

## EPIC 3 — Data Ingestion

### Feature 3.1 — Product Scraping
T46 — Create Scrapy project
T47 — Identify target website
T48 — Scrape product names
T49 — Scrape images
T50 — Scrape categories
T51 — Export JSON

### Feature 3.2 — Product Insertion
T52 — Create family insertion script
T53 — Create product insertion script
T54 — Create image insertion script

### Feature 3.3 — Sales Generation
T55 — Generate sales dataset
T56 — Add realistic distribution (quantity)
T57 — Add simple seasonality
T58 — Load sales into DB

## EPIC 4 — FastAPI API

### Feature 4.1 — API Setup
T59 — Create FastAPI app
T60 — Add /health route
T61 — Test server startup

### Feature 4.2 — SQLAlchemy Models
T62 — Create Product model
T63 — Create Price model
T64 — Create Promotion model
T65 — Create SalesTransaction model

### Feature 4.3 — Read Endpoints
T66 — Endpoint GET /products
T67 — Endpoint GET /prices
T68 — Endpoint GET /promotions
T69 — Endpoint GET /sales

### Feature 4.4 — KPIs
T70 — Endpoint /kpis
T71 — Revenue computation
T72 — Volume computation

### Feature 4.5 — Anomalies
T73 — Endpoint /anomalies
T74 — Detect sales drop
T75 — Detect overperformance

### Feature 4.6 — Pricing Workflow
T76 — Endpoint POST /price-change-request
T77 — Endpoint GET /price-change-request
T78 — Endpoint POST /approve-request

## EPIC 5 — Data Analytics (dbt)

### Feature 5.1 — dbt Setup
T79 — Initialize dbt project
T80 — Configure PostgreSQL connection
T81 — Test dbt run

### Feature 5.2 — obt_sales
T82 — Create obt_sales model
T83 — Join sales + prices
T84 — Add promotions
T85 — Add product family

### Feature 5.3 — Price KPI
T86 — Create kpi_price_performance model
T87 — Before / after computation
T88 — Country benchmark computation

### Feature 5.4 — Promo KPI
T89 — Create kpi_promo_performance model
T90 — Baseline computation
T91 — Acceleration computation


## EPIC 6 — Django Frontend

### Feature 6.1 — Django Setup
T92 — Create Django project
T93 — Install Tailwind
T94 — Configure theme

### Feature 6.2 — Main Pages
T95 — Dashboard page
T96 — Products page
T97 — Prices page
T98 — Promotions page

### Feature 6.3 — Workflow UI
T99 — Price change form
T100 — Request list
T101 — Validation page


## EPIC 6 (suite) — Analytics Frontend

### Feature 6.4 — Exposition de pct_analytics dans le frontend
T113 — Endpoint GET /analytics/sales (OBT enrichi filtrable)
T114 — Endpoint GET /analytics/sales/summary (agrégats par produit)
T115 — Page Ventes Analytiques (/analytique/ventes/) avec filtres pays/magasin/promo
T116 — Sidebar produit enrichie avec KPIs analytiques (CA, quantité, part promo, période)
T117 — Refonte page Anomalies en cards + panel latéral avec actions
T118 — Lien Ventes Analytiques dans sidebar base.html (desktop + mobile)

### Feature 6.5 — Amélioration détection d'anomalies [BACKLOG]
**Problème** : Le seuil `min_revenue = 500 €` est arbitraire et non adaptatif.
**Objectif** : Remplacer la règle fixe par une détection statistique calculée depuis `pct_analytics.obt_sales`.
**Travaux à réaliser** :
- Calculer la distribution du CA par promotion (moyenne, écart-type, percentiles)
- Flaguer une promo si CA < percentile 10 ou à plus de 2 écarts-types sous la moyenne
- Pondérer par famille produit
- Ajouter de nouveaux types d'anomalies : prix de vente > prix référence, écart anormal entre magasins
**Fichiers** : `anomaly_service.py`, `routes/anomalies.py`, éventuellement nouveau modèle dbt `kpi_anomaly_detection`
**Complexité estimée** : Moyenne (1–2 jours)

## EPIC 7 — AI Chatbot

### Feature 7.1 — AI Service Setup
T102 — Create Python AI service
T103 — Connect read-only DB

### Feature 7.2 — AI Functions
T104 — Explain KPIs
T105 — Explain anomalies
T106 — Suggest actions

## EPIC 8 — CI/CD & Monitoring

### Feature 8.1 — CI/CD
T107 — Add GitHub Actions
T108 — Add backend tests
T109 — Add linting

### Feature 8.2 — Monitoring
T110 — API logs
T111 — Error logs
T112 — Health checks

## EPIC 9 — Observability & Operations

### Feature 9.1 — Prometheus Metrics
T181 — Add Prometheus metrics to backend (http_requests_total, http_responses_total, http_request_duration_seconds)
T182 — Add Prometheus metrics to frontend (django_http_requests_total, django_http_responses_total, django_http_request_duration_seconds)
T183 — Add Prometheus metrics to AI service (ai_requests_total, ai_chat_requests_total, ai_chat_responses_total, ai_errors_total)

### Feature 9.2 — Incident Simulation & Diagnosis
T184 — Define and reproduce backend connectivity failure scenario (invalid BACKEND_API_URL)
T185 — Execute monitoring-driven diagnosis: Prometheus, metrics, logs
T186 — Apply resolution and validate return to normal state

### Feature 9.3 — Operations Documentation
T187 — Create application operations runbook (docs/07_operations/application_operations_runbook.md)
T188 — Create database backup and restore runbook (docs/07_operations/database_backup_restore_runbook.md)
T189 — Create application maintenance runbook (docs/07_operations/application_maintenance_runbook.md)

### Feature 9.4 — Validation & Reporting
T190 — Validate complete monitoring stack end-to-end (all services, Prometheus, Grafana, logs)
T191 — Write full incident report consolidating T184–T186 and T190

## Definition of Done (global)

A ticket is considered done if:

- code written
- tested locally
- no errors
- consistent with architecture
- documented if necessary
