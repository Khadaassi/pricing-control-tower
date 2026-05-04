# Data Flow — Pricing Control Tower

## 1. Vue d'ensemble du flux de données

```
┌───────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Scripts Python   │────▶│   pct_core       │────▶│   pct_analytics     │
│  (génération)     │     │   (PostgreSQL)   │     │   (vues dbt)        │
└───────────────────┘     └──────────────────┘     └─────────────────────┘
        │                         │                         │
   seed_reference_data.py         │                    obt_sales
   generate_sales_dataset.py      │                    kpi_price_performance
   load_sales_transactions.py     │                         │
                                  │                         ▼
                           ┌──────▼──────┐          ┌──────────────┐
                           │  FastAPI    │          │  Frontend    │
                           │  (Backend)  │◀─────────│  (Django)    │
                           └─────────────┘          └──────────────┘
```

---

## 2. Flux d'ingestion (données → pct_core)

### Étape 1 : Seed des données de référence

**Script** : `data/generation/seed_reference_data.py`

Insère les données de référence dans `pct_core` :
- Pays (country)
- Magasins (store)
- Familles de produits (product_family)
- Produits (product)
- Prix standards et promotionnels (price)
- Promotions (promotion)

### Étape 2 : Génération du dataset de ventes

**Script** : `data/generation/generate_sales_dataset.py`

Génère un fichier CSV (`data/generated/sales_transactions.csv`) contenant ~20 000 transactions simulées sur 6 mois.

Règles de génération :
- Distribution non uniforme des quantités (variabilité produit + magasin + effet promo)
- Saisonnalité simple
- Cohérence avec les prix et promotions actifs à chaque date

### Étape 3 : Chargement en base

**Script** : `data/generation/load_sales_transactions.py`

Charge le CSV dans la table `pct_core.sales_transaction`.

---

## 3. Flux de transformation (pct_core → pct_analytics via dbt)

### Pipeline dbt

```
pct_core (source)
    │
    ▼
STAGING (renommage, typage)
    stg_sales, stg_product, stg_product_family,
    stg_store, stg_country, stg_price, stg_promotion
    │
    ▼
INTERMEDIATE (enrichissement, jointures)
    int_sales_enriched
    │
    ▼
MARTS (agrégation, KPI)
    obt_sales              → Table dénormalisée complète
    kpi_price_performance  → KPI glissant 30j + benchmark pays
```

### Détail des transformations

| Couche | Modèle | Transformation |
|---|---|---|
| Staging | `stg_*` | Sélection des colonnes, renommage, typage |
| Intermediate | `int_sales_enriched` | Jointure ventes × produit × magasin × prix × promotion. Calcul `price_difference`, `price_difference_rate`, flags booléens |
| Mart | `obt_sales` | Ajout familles, pays, classification temporelle promotion |
| Mart | `kpi_price_performance` | Périodisation 30j, agrégation par (country, store, product), benchmark pays, flags métier |

---

## 4. Flux de consommation (pct_analytics → API → Frontend)

### Backend (FastAPI)

L'API expose les données de `pct_core` via des endpoints REST :
- `GET /products` — Référentiel produits
- `GET /prices` — Prix standards et promotionnels
- `GET /promotions` — Promotions actives et historiques

Les KPI issus de `pct_analytics` sont consommables via des endpoints dédiés (évolution).

### Frontend (Django)

Consomme l'API REST pour afficher :
- Tableaux de bord
- Listes de produits et prix
- Indicateurs de performance

---

## 5. Dépendances du flux

| Étape | Prérequis |
|---|---|
| Seed référentiel | PostgreSQL opérationnel, schéma `pct_core` créé |
| Génération ventes | Référentiel inséré (produits, magasins, prix, promos) |
| Chargement ventes | CSV généré |
| dbt run | Données présentes dans `pct_core`, schéma `pct_analytics` créé |
| API | PostgreSQL accessible |
| Frontend | API accessible |

---

## 6. Commandes d'exécution

```bash
# 1. Démarrer PostgreSQL
cd backend && docker compose up -d

# 2. Appliquer les migrations
alembic upgrade head

# 3. Seed des données de référence
python data/generation/seed_reference_data.py

# 4. Générer les ventes
python data/generation/generate_sales_dataset.py

# 5. Charger les ventes
python data/generation/load_sales_transactions.py

# 6. Exécuter dbt
cd data/dbt && dbt run

# 7. Lancer l'API
cd backend && uvicorn app.main:app --reload
```