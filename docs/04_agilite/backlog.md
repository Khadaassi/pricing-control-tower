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

## EPIC 10 — E3 Certification Remediation (C9 / C10 / C12 / C13)

Tickets issus de la revue documentaire du rapport `docs/08_certification/E3_rapport_api_modele_ia.md` : chaque écart a été vérifié dans le code avant d'être transformé en ticket, pour ne pas confondre un défaut de rédaction avec un vrai développement manquant.

### Feature 10.1 — C9 : Authentifier `POST /chat` (Django → ai_service) [BACKLOG]
**Problème** : `ai_service/app/api/routes/chat.py::chat()` n'a aucune dépendance de sécurité ni vérification d'en-tête, et `frontend/core/services/ai_chatbot_client.py::ask_chatbot()` envoie le payload JSON sans en-tête `Authorization`. La grille C9 exige explicitement un moyen d'authentification de l'API IA.
**Objectif** : Authentifier le flux `Django → ai_service` en réutilisant le mécanisme de jeton signé déjà en place dans l'autre sens (`ai_service → backend`, `app/core/internal_auth.py::issue_service_token`, `INTERNAL_AUTH_SECRET`), plutôt que d'introduire un second mécanisme.
**Travaux à réaliser** :
- Ajouter côté frontend une émission de jeton (miroir de `frontend/services/internal_auth.py::issue_service_token`) et l'envoyer en en-tête `Authorization: Bearer <jeton>` depuis `ask_chatbot()`.
- Ajouter côté `ai_service` une fonction de vérification de jeton (`app/core/internal_auth.py`, il n'existe aujourd'hui que l'émission) exposée comme dépendance FastAPI (`Depends(...)`) sur `POST /chat`.
- Retourner `401` si l'en-tête est absent, `403` si le jeton est invalide ou expiré.
- Ajouter les tests : jeton valide → `200` ; en-tête absent → `401` ; jeton invalide/expiré → `403`.
**Fichiers** : `ai_service/app/api/routes/chat.py`, `ai_service/app/core/internal_auth.py`, `frontend/core/services/ai_chatbot_client.py`, `frontend/services/internal_auth.py`, tests associés dans `ai_service/tests/api/`.
**Complexité estimée** : Moyenne (0,5–1 jour) — le mécanisme JWT existe déjà dans l'autre sens, il s'agit de le répliquer et de l'appliquer à cet endpoint.
**Definition of Done** :
- Appel `POST /chat` avec jeton valide → `200`.
- Appel sans en-tête `Authorization` → `401`.
- Appel avec jeton invalide/expiré → `403`.
- Tests automatisés ajoutés et passants (succès + les deux cas de refus).
- `docs/08_certification/E3_rapport_api_modele_ia.md` §2.4 mis à jour avec preuve `curl`/Swagger réelle.

### Feature 10.2 — C13 : Automatiser le déploiement vers la VM GCP [FAIT]

**Statut (26/08/2026)** : job `deploy-gcp` validé avec succès en conditions réelles — run GitHub Actions #151 (commit `00efb8c`, push sur `feature/gcp-deployment`), tous les jobs verts dont `Deploy to GCP (pct-app-vm)`, health checks post-déploiement confirmés indépendamment (`/health` frontend et `/api/health` Grafana → `200`). Trois corrections IAM/exploitation ont été nécessaires en cours de route (détaillées dans `docs/08_certification/E3_rapport_api_modele_ia.md` §6.6) : `roles/iam.serviceAccountUser` sur `pct-vm-sa`, `roles/compute.osAdminLogin` pour le déployeur, et exécution de `git pull`/`fetch-secrets.sh` sous `sudo` (le compte OS Login du déployeur CI n'a pas les mêmes droits que l'opérateur humain sur `/opt/pct`). DoD satisfaite.
**Problème** : `.github/workflows/ci.yml` ne contient aucun job de déploiement (pas de `gcloud`/`ssh`/`scp`/`workflow_dispatch`). Le déploiement vers la VM GCP se fait aujourd'hui manuellement, suivant `docs/07_operations/gcp_exploitation_runbook.md` §4. La grille C13 exige explicitement que validation, tests, packaging **et déploiement** soient automatisés.
**Objectif** : Ajouter un job de déploiement automatisé déclenché après packaging réussi, reproduisant la procédure manuelle déjà documentée et validée.
**Travaux à réaliser** :
- Ajouter un job `deploy` à `.github/workflows/ci.yml`, dépendant de `docker-build`, déclenché sur push vers `main` et/ou via `workflow_dispatch`.
- Stocker les identifiants nécessaires (clé du compte de service `pct-vm-sa` ou clé SSH) en secrets GitHub Actions.
- Reproduire dans ce job les étapes du runbook d'exploitation (pull, rebuild, redeploy Docker Compose sur la VM).
- Ajouter une vérification post-déploiement (health check sur `/chat/health` et `/health` backend) qui fait échouer le job en cas de service dégradé.
**Fichiers** : `.github/workflows/ci.yml`, éventuellement un script dédié type `scripts/deploy_gcp.sh`.
**Complexité estimée** : Moyenne à élevée (1–2 jours) — gestion des secrets CI, connexion SSH depuis GitHub Actions, idempotence du redéploiement.
**Definition of Done** :
- Un déploiement déclenché depuis GitHub Actions met à jour effectivement le service sur la VM GCP.
- Le job échoue si le health check post-déploiement échoue.
- Capture d'une exécution réussie ajoutée à `docs/08_certification/E3_rapport_api_modele_ia.md` §6.6.

### Feature 10.3 — C12 : Mesurer et documenter la couverture de tests [FAIT]

**Statut (26/08/2026)** : `pytest-cov` intégré, couverture mesurée à 81,23 %, seuil `fail_under = 80` fixé après coup dans `pyproject.toml` et appliqué dans le job CI `ai-service-tests` (bloque la fusion en cas de régression). Détail par module et analyse I/O vs. logique métier dans `docs/08_certification/E3_rapport_api_modele_ia.md` §5.4. DoD satisfaite.
**Problème** : `pytest-cov` n'est pas déclaré dans les dépendances de `ai_service/pyproject.toml` ; aucune mesure de couverture n'existe. La grille C12 demande explicitement un objectif de couverture et une procédure de calcul documentée.
**Objectif** : Outiller la mesure de couverture, obtenir un chiffre réel, puis fixer un objectif cohérent avec ce chiffre — pas l'inverse.
**Travaux à réaliser** :
- `uv add --dev pytest-cov` dans `ai_service`.
- Exécuter `uv run pytest --cov=app --cov-report=term-missing` et consigner le résultat obtenu.
- Identifier les modules sous-couverts (probablement `app/orchestrator`, `app/tools`, `app/rag`, `app/api`) et compléter les tests si nécessaire.
- Fixer un objectif de couverture documenté, justifié par le résultat mesuré.
- Optionnel : ajouter l'étape de couverture au job `ai-service-tests` de la CI.
**Fichiers** : `ai_service/pyproject.toml`, `.github/workflows/ci.yml` (optionnel), `docs/08_certification/E3_rapport_api_modele_ia.md` §5.4.
**Complexité estimée** : Faible pour la mesure initiale (quelques heures) ; variable selon les lacunes de couverture identifiées.
**Definition of Done** :
- `pytest-cov` intégré, exécutable localement (et en CI si retenu).
- Rapport de couverture réel obtenu et analysé.
- Objectif de couverture documenté avec sa justification (pas de chiffre fixé a priori).
- `docs/08_certification/E3_rapport_api_modele_ia.md` §5.4 mis à jour avec le résultat réel.

### Feature 10.4 — C10 : Corriger l'accessibilité de l'interface chatbot [FAIT]

**Statut (26/08/2026)** : les trois attributs (`aria-label` sur les deux boutons icône, `role="log" aria-live="polite"` sur l'historique) ajoutés à `chatbot.html` et vérifiés dans le HTML réellement rendu par Django (`render_to_string` + `RequestFactory`). Reste à faire en soutenance : démonstration clavier/lecteur d'écran live, audit de contraste. DoD partiellement satisfaite (le code est fait et vérifié par rendu ; la démonstration live reste un acte de soutenance, pas un développement).
**Problème** : audit de `frontend/core/templates/core/chatbot.html` (E3 §3.4) — le bouton d'envoi (`#chatbot-send`) n'a ni `aria-label` ni texte visible, le bouton d'effacement (`#chatbot-page-clear`) n'a qu'un `title` sans `aria-label`, et la zone `#chatbot-history` n'a pas de région `aria-live` pour annoncer les nouveaux messages aux lecteurs d'écran.
**Objectif** : Fermer les deux écarts d'accessibilité identifiés, qui sont des corrections ciblées et non structurelles.
**Travaux à réaliser** :
- Ajouter `aria-label="Envoyer la question"` sur `#chatbot-send`.
- Ajouter `aria-label="Effacer la conversation"` sur `#chatbot-page-clear`.
- Ajouter `aria-live="polite"` sur `#chatbot-history` pour l'annonce des nouveaux messages assistant.
- Réaliser et documenter un test clavier manuel (Tab, Entrée, focus visible sur tous les contrôles).
**Fichiers** : `frontend/core/templates/core/chatbot.html`.
**Complexité estimée** : Très faible (moins d'une heure de développement ; le reste est vérification et documentation).
**Definition of Done** :
- Les deux boutons ont un nom accessible vérifiable (ex. via l'arbre d'accessibilité du navigateur).
- `#chatbot-history` annonce les nouveaux messages via `aria-live`.
- Test clavier manuel réalisé et documenté.
- `docs/08_certification/E3_rapport_api_modele_ia.md` §3.4 mis à jour pour refléter l'état corrigé.

### Feature 10.5 — C11 : Opérationnaliser les seuils d'alerte [FAIT]

**Problème** : les seuils documentés en E3 §4.5 n'étaient reliés à aucune règle Prometheus, aucun Alertmanager, aucune alerte réelle — un seuil documenté n'est pas une alerte.
**Statut (26/08/2026)** : `monitoring/prometheus/alert_rules.yml` (5 règles couvrant les seuils déjà documentés), chargé via `rule_files:` dans `prometheus.yml`, service `alertmanager` ajouté à `docker-compose.yml` et `infra/compose/docker-compose.gcp.yml` (config `monitoring/alertmanager/alertmanager.yml`), port 9093 ouvert en IAP-only dans `infra/terraform/firewall.tf` (appliqué en production). Cycle complet `pending → firing → resolved` observé et vérifié via les API Prometheus/Alertmanager en conditions réelles (détail dans `docs/08_certification/E3_rapport_api_modele_ia.md` §4.5). Aucun canal de notification externe (e-mail/Slack) configuré — pas d'identifiants disponibles pour ce MVP, documenté comme tel plutôt que simulé.
**Fichiers** : `monitoring/prometheus/alert_rules.yml`, `monitoring/alertmanager/alertmanager.yml`, `docker-compose.yml`, `infra/compose/docker-compose.gcp.yml`, `infra/terraform/firewall.tf`.
**DoD** : règle réelle déclenchée en environnement de test, état firing puis resolved observé, notification (Alertmanager) confirmée. Satisfaite.

## Definition of Done (global)

A ticket is considered done if:

- code written
- tested locally
- no errors
- consistent with architecture
- documented if necessary
