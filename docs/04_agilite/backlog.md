BACKLOG COMPLET (ATOMIQUE)

## EPIC 1 — Setup projet & environnement

### Feature 1.1 — Initialisation repo
T1 — Créer repo GitHub
T2 — Ajouter README.md
T3 — Ajouter .gitignore Python
T4 — Initialiser git flow (branches main/dev)

### Feature 1.2 — Structure projet
T5 — Créer dossier /backend
T6 — Créer dossier /frontend
T7 — Créer dossier /data
T8 — Créer dossier /docs
T9 — Créer sous-dossiers docs (functional, data_model, architecture, agile)

### Feature 1.3 — Environnement Python
T10 — Initialiser environnement uv
T11 — Créer fichier pyproject.toml
T12 — Installer FastAPI
T13 — Installer Uvicorn
T14 — Installer SQLAlchemy
T15 — Installer Alembic
T16 — Installer psycopg2 / asyncpg


## EPIC 2 — Base de données PostgreSQL

### Feature 2.1 — Setup PostgreSQL
T17 — Ajouter PostgreSQL dans docker-compose
T18 — Configurer variables d’environnement DB
T19 — Vérifier connexion DB (psql)
T20 — Créer database pct

### Feature 2.2 — Création des schémas
T21 — Créer schema pct_core
T22 — Créer schema pct_analytics
T23 — Vérifier présence via psql

### Feature 2.3 — Alembic setup
T24 — Initialiser Alembic
T25 — Configurer connection string
T26 — Tester migration vide

### Feature 2.4 — Tables référentiel
T27 — Créer table country
T28 — Créer table store
T29 — Créer table product_family
T30 — Créer table product
T31 — Créer table product_image

### Feature 2.5 — Tables utilisateurs & audit
T32 — Créer table app_user
T33 — Créer table audit_log

### Feature 2.6 — Tables pricing
T34 — Créer table promotion
T35 — Créer table price
T36 — Ajouter contraintes CHECK price_scope
T37 — Ajouter contraintes CHECK price_type
T38 — Ajouter contrainte promo ↔ price_type

### Feature 2.7 — Workflow pricing
T39 — Créer table price_change_request
T40 — Ajouter colonne scope
T41 — Ajouter FK approved_price_id

### Feature 2.8 — Historisation
T42 — Créer table price_history

### Feature 2.9 — Transactions
T43 — Créer table sales_transaction
T44 — Ajouter contraintes CHECK quantité
T45 — Ajouter contraintes CHECK prix

## EPIC 3 — Data ingestion

### Feature 3.1 — Scraping produits
T46 — Créer projet Scrapy
T47 — Identifier site cible
T48 — Scraper noms produits
T49 — Scraper images
T50 — Scraper catégories
T51 — Export JSON

### Feature 3.2 — Insertion produits
T52 — Créer script insertion familles
T53 — Créer script insertion produits
T54 — Créer script insertion images

### Feature 3.3 — Génération ventes
T55 — Générer dataset ventes
T56 — Ajouter distribution réaliste (quantité)
T57 — Ajouter saisonnalité simple
T58 — Charger ventes en DB

## EPIC 4 — API FastAPI

### Feature 4.1 — Setup API
T59 — Créer app FastAPI
T60 — Ajouter route /health
T61 — Tester lancement serveur

### Feature 4.2 — Models SQLAlchemy
T62 — Créer modèle Product
T63 — Créer modèle Price
T64 — Créer modèle Promotion
T65 — Créer modèle SalesTransaction

### Feature 4.3 — Endpoints lecture
T66 — Endpoint GET /products
T67 — Endpoint GET /prices
T68 — Endpoint GET /promotions
T69 — Endpoint GET /sales

### Feature 4.4 — KPI
T70 — Endpoint /kpis
T71 — Calcul CA
T72 — Calcul volume

### Feature 4.5 — Anomalies
T73 — Endpoint /anomalies
T74 — Détecter baisse ventes
T75 — Détecter surperformance

### Feature 4.6 — Workflow pricing
T76 — Endpoint POST /price-change-request
T77 — Endpoint GET /price-change-request
T78 — Endpoint POST /approve-request

## EPIC 5 — Data analytics (dbt)

### Feature 5.1 — Setup dbt
T79 — Initialiser projet dbt
T80 — Configurer connexion PostgreSQL
T81 — Tester dbt run

### Feature 5.2 — obt_sales
T82 — Créer modèle obt_sales
T83 — Joindre ventes + prix
T84 — Ajouter promo
T85 — Ajouter famille produit

### Feature 5.3 — KPI prix
T86 — Créer modèle kpi_price_performance
T87 — Calcul before / after
T88 — Calcul benchmark pays

### Feature 5.4 — KPI promo
T89 — Créer modèle kpi_promo_performance
T90 — Calcul baseline
T91 — Calcul accélération


## EPIC 6 — Frontend Django

### Feature 6.1 — Setup Django
T92 — Créer projet Django
T93 — Installer Tailwind
T94 — Configurer thème

### Feature 6.2 — Pages principales
T95 — Page dashboard
T96 — Page produits
T97 — Page prix
T98 — Page promotions

### Feature 6.3 — Workflow UI
T99 — Formulaire changement prix
T100 — Liste des demandes
T101 — Page validation


## EPIC 7 — Chatbot IA

### Feature 7.1 — Setup service IA
T102 — Créer service Python IA
T103 — Connecter DB lecture seule

### Feature 7.2 — Fonctions IA
T104 — Expliquer KPI
T105 — Expliquer anomalies
T106 — Suggérer actions

##EPIC 8 — CI/CD & Monitoring

### Feature 8.1 — CI/CD
T107 — Ajouter GitHub Actions
T108 — Ajouter tests backend
T109 — Ajouter lint

### Feature 8.2 — Monitoring
T110 — Logs API
T111 — Logs erreurs
T112 — Health checks

## Definition of Done (global)

Un ticket est terminé si :

code écrit
testé localement
pas d’erreur
cohérent avec architecture
documenté si nécessaire
