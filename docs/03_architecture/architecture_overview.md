# Architecture Overview — Pricing Control Tower

## 1. Vue d'ensemble

Le projet Pricing Control Tower est organisé en couches indépendantes communicant via des interfaces bien définies :

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
│  │ (transac.)  │──dbt────▶│ (vues analytiques)│    │
│  └─────────────┘          └──────────────────┘     │
└─────────────────────────────────────────────────────┘
```

---

## 2. Composants

| Composant | Technologie | Rôle |
|---|---|---|
| **Backend** | FastAPI + SQLAlchemy | API REST, logique métier, accès données transactionnelles |
| **Frontend** | Django + Tailwind CSS | Interface utilisateur, rendu serveur (SSR) |
| **Base de données** | PostgreSQL 16 | Stockage transactionnel (`pct_core`) et analytique (`pct_analytics`) |
| **Transformation** | dbt (dbt-postgres) | Pipeline de transformation : staging → intermediate → marts |
| **Génération de données** | Python (scripts) | Simulation de ventes réalistes pour le MVP |
| **Conteneurisation** | Docker Compose | Orchestration locale (PostgreSQL) |

---

## 3. Schémas de base de données

### `pct_core` — Données transactionnelles

Géré par Alembic (migrations versionnées). Contient :

- `country`, `store` — Référentiel géographique
- `product_family`, `product`, `product_image` — Référentiel produit
- `price` — Prix (standard et promotionnel)
- `promotion` — Promotions
- `sales_transaction` — Transactions de vente
- `user_account` — Utilisateurs

### `pct_analytics` — Données analytiques

Géré par dbt. Contient des vues matérialisées :

- **Staging** : `stg_sales`, `stg_product`, `stg_store`, `stg_country`, `stg_price`, `stg_promotion`, `stg_product_family`
- **Intermediate** : `int_sales_enriched`
- **Marts** : `obt_sales`, `kpi_price_performance`

---

## 4. Organisation du code

```
princing-control-tower/
├── backend/              # API FastAPI + migrations Alembic
│   ├── app/              # Code applicatif (routes, modèles, schémas)
│   ├── alembic/          # Migrations de schéma pct_core
│   ├── tests/            # Tests unitaires et intégration
│   └── docker-compose.yml
├── data/                 # Couche data
│   ├── dbt/              # Projet dbt (staging, intermediate, marts)
│   ├── generated/        # Fichiers CSV générés
│   └── generation/       # Scripts de génération de données
├── docs/                 # Documentation complète
│   ├── 01_functional/    # Cahier des charges
│   ├── 02_data_model/    # MCD, MLD, MPD
│   ├── 03_architecture/  # Architecture, flux, choix techniques
│   ├── 04_agilite/       # Backlog, epics, user stories
│   └── 05_runbook/       # Installation, déploiement, monitoring
└── frontend/             # Application Django (à venir)
```

---

## 5. Communication entre composants

| Source | Destination | Protocole | Description |
|---|---|---|---|
| Frontend | Backend | HTTP REST | Consommation des endpoints API |
| Backend | PostgreSQL | SQL (asyncpg) | CRUD sur `pct_core` |
| dbt | PostgreSQL | SQL | Lecture `pct_core`, écriture `pct_analytics` |
| Scripts génération | PostgreSQL | SQL (psycopg2) | Insertion des données simulées |

---

## 6. Principes d'architecture

- **Séparation des responsabilités** : chaque composant a un rôle unique
- **Couche analytique en lecture seule** : dbt ne modifie jamais `pct_core`
- **Données simulées reproductibles** : seed fixe pour la génération
- **Migrations versionnées** : Alembic pour toute modification de schéma
- **API stateless** : pas de session côté serveur