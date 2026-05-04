# Run Local — Guide d'exécution locale

## Prérequis

- Python 3.11+
- Docker & Docker Compose
- uv (gestionnaire de packages Python)
- Git

---

## 1. Cloner le projet

```bash
git clone <repo_url>
cd princing-control-tower
```

---

## 2. Démarrer PostgreSQL

```bash
cd backend
docker compose up -d
```

Vérification :

```bash
docker compose exec postgres psql -U pct_user -d pct -c "SELECT 1;"
```

---

## 3. Configurer l'environnement Python

```bash
cd backend
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

---

## 4. Variables d'environnement

Créer un fichier `backend/.env` :

```env
POSTGRES_USER=pct_user
POSTGRES_PASSWORD=pct_password
POSTGRES_DB=pct
DATABASE_URL=postgresql://pct_user:pct_password@localhost:5432/pct
```

---

## 5. Appliquer les migrations

```bash
cd backend
alembic upgrade head
```

Cela crée le schéma `pct_core` et toutes les tables (country, store, product, price, promotion, sales_transaction, etc.).

---

## 6. Charger les données de référence

```bash
python data/generation/seed_reference_data.py
```

Insère les utilisateurs, pays, magasins, familles, produits, promotions et prix.

---

## 7. Générer et charger les ventes

```bash
# Génération du CSV
python data/generation/generate_sales_dataset.py

# Chargement en base
python data/generation/load_sales_transactions.py
```

Le fichier généré est `data/generated/sales_transactions.csv` (~20 000 lignes).

---

## 8. Exécuter dbt

```bash
cd data/dbt
dbt run
```

Cela crée les vues dans le schéma `pct_analytics` :
- `stg_*` (staging)
- `int_sales_enriched` (intermediate)
- `obt_sales` (mart — OBT)
- `kpi_price_performance` (mart — KPI)

### Tests dbt

```bash
dbt test
```

---

## 9. Lancer l'API

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

L'API est accessible sur `http://localhost:8000`.

Documentation interactive : `http://localhost:8000/docs`

---

## 10. Vérifications rapides

```bash
# Santé de l'API
curl http://localhost:8000/health

# Liste des produits
curl http://localhost:8000/products

# KPI depuis psql
docker compose exec postgres psql -U pct_user -d pct \
  -c "SELECT * FROM pct_analytics.kpi_price_performance LIMIT 5;"
```

---

## Résumé des commandes

| Étape | Commande |
|---|---|
| PostgreSQL | `cd backend && docker compose up -d` |
| Migrations | `cd backend && alembic upgrade head` |
| Seed référentiel | `python data/generation/seed_reference_data.py` |
| Génération ventes | `python data/generation/generate_sales_dataset.py` |
| Chargement ventes | `python data/generation/load_sales_transactions.py` |
| dbt | `cd data/dbt && dbt run` |
| Tests dbt | `cd data/dbt && dbt test` |
| API | `cd backend && uvicorn app.main:app --reload` |