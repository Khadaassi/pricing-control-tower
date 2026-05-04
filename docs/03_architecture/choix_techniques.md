# Choix Techniques — Pricing Control Tower

## 1. Backend

| Technologie | Version | Justification |
|---|---|---|
| **Python** | 3.11+ | Langage principal — écosystème data et IA mature |
| **FastAPI** | 0.100+ | Framework API moderne, typage natif, documentation auto (OpenAPI) |
| **SQLAlchemy** | 2.x | ORM robuste, support async, mapping déclaratif |
| **Alembic** | 1.x | Migrations versionnées, intégration native SQLAlchemy |
| **uv** | — | Gestionnaire de packages rapide, remplacement de pip |
| **Pydantic** | 2.x | Validation des données, sérialisation, schémas API |

---

## 2. Base de données

| Technologie | Version | Justification |
|---|---|---|
| **PostgreSQL** | 16 | SGBD relationnel performant, support JSON, CTE, window functions |
| **Docker Compose** | — | Orchestration locale simple et reproductible |

### Organisation des schémas

| Schéma | Rôle | Gestion |
|---|---|---|
| `pct_core` | Données transactionnelles et référentiel | Alembic (migrations) |
| `pct_analytics` | Vues analytiques et KPI | dbt (transformations) |

---

## 3. Data / Analytics

| Technologie | Version | Justification |
|---|---|---|
| **dbt** (dbt-core + dbt-postgres) | 1.8+ | Transformation SQL versionnée, tests intégrés, documentation auto |
| **Python (scripts)** | — | Génération de données simulées reproductibles |

### Architecture dbt

- **Staging** : extraction et renommage depuis les sources `pct_core`
- **Intermediate** : enrichissement par jointures (ventes × dimensions)
- **Marts** : tables dénormalisées (`obt_sales`) et KPI (`kpi_price_performance`)

### Choix de modélisation analytique

- **OBT (One Big Table)** : approche dénormalisée adaptée au volume MVP (~20k lignes)
- **Périodisation glissante** : comparaison 30 jours vs 30 jours précédents (pas de calendrier fiscal)
- **Benchmark pays** : prix moyen pondéré par volume au niveau country × product

---

## 4. Frontend

| Technologie | Justification |
|---|---|
| **Django** | Framework full-stack Python, rendu serveur (SSR), admin intégré |
| **Tailwind CSS** | Utility-first CSS, rapidité de développement, design responsive |

---

## 5. Infrastructure

| Technologie | Justification |
|---|---|
| **Docker** | Conteneurisation pour la reproductibilité |
| **Docker Compose** | Orchestration locale (PostgreSQL) |
| **GCP Cloud Run** (cible) | Déploiement cloud serverless |

---

## 6. Qualité et Tests

| Outil | Rôle |
|---|---|
| **pytest** | Tests unitaires et intégration backend |
| **dbt test** | Tests de données (not_null, unique, accepted_values) |
| **GitHub Actions** (cible) | CI/CD automatisée |

---

## 7. Décisions clés

| Décision | Raison |
|---|---|
| PostgreSQL unique (core + analytics) | Simplicité MVP, pas de datawarehouse séparé nécessaire |
| dbt en vues (pas de tables matérialisées) | Volume faible, rafraîchissement instantané |
| Génération Python plutôt que Faker | Contrôle total de la distribution et reproductibilité (seed fixe) |
| API stateless | Scalabilité, simplicité, pas de gestion de session |
| Séparation backend/data/frontend | Indépendance des déploiements, responsabilités claires |