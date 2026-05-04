# MLD — Schéma analytique `pct_analytics`

## 1. Objectif

Ce modèle logique de données décrit la structure du schéma `pct_analytics`, construit par dbt à partir des données transactionnelles du schéma `pct_core`.

Il sert de référence pour :

* comprendre la couche analytique du projet
* documenter les modèles dbt (staging → intermediate → marts)
* guider l'interprétation des KPI

---

## 2. Architecture des modèles dbt

```
sources (pct_core)
    │
    ├── stg_sales
    ├── stg_product
    ├── stg_product_family
    ├── stg_store
    ├── stg_country
    ├── stg_price
    └── stg_promotion
            │
            ▼
    intermediate
    └── int_sales_enriched
            │
            ▼
    marts
    ├── obt_sales
    ├── kpi_price_performance
    └── kpi_promo_performance
```

---

## 3. Couche Staging

Les modèles staging extraient et renomment les colonnes depuis les tables source `pct_core`.

| Modèle | Source | Description |
|---|---|---|
| `stg_sales` | `pct_core.sales_transaction` | Transactions de vente brutes |
| `stg_product` | `pct_core.product` | Référentiel produit |
| `stg_product_family` | `pct_core.product_family` | Familles de produits |
| `stg_store` | `pct_core.store` | Référentiel magasin |
| `stg_country` | `pct_core.country` | Référentiel pays |
| `stg_price` | `pct_core.price` | Référentiel prix |
| `stg_promotion` | `pct_core.promotion` | Référentiel promotions |

---

## 4. Couche Intermediate

### 4.1 `int_sales_enriched`

Jointure des ventes avec les dimensions produit, magasin, prix et promotion.

| Champ | Description |
|---|---|
| `transaction_id` | PK — identifiant unique de la vente |
| `transaction_date` | Date et heure de la transaction |
| `product_id`, `product_code`, `product_name` | Dimensions produit |
| `brand`, `model`, `product_family_id` | Attributs produit |
| `store_id`, `store_code`, `store_name` | Dimensions magasin |
| `country_id`, `city`, `region` | Dimensions géographiques |
| `price_id`, `price_amount`, `currency_code` | Prix de référence |
| `price_effective_from`, `price_effective_to` | Période de validité du prix |
| `price_scope` | `COUNTRY` ou `STORE` |
| `price_type` | `STANDARD` ou `PROMO` |
| `is_store_specific_price` | Booléen — prix magasin spécifique |
| `is_promotional_price` | Booléen — prix promotionnel |
| `is_price_temporally_valid` | Booléen — validité temporelle du prix |
| `price_difference` | Écart entre prix payé et prix de référence |
| `price_difference_rate` | Taux d'écart prix payé vs référence |
| `promotion_id`, `promotion_code`, `promotion_name` | Dimensions promotion |
| `discount_type`, `discount_value` | Type et valeur de remise |
| `promotion_start_date`, `promotion_end_date` | Période promotion |
| `quantity`, `unit_price`, `revenue` | Mesures transactionnelles |
| `is_promo` | Booléen — transaction liée à une promo |

---

## 5. Couche Marts

### 5.1 `obt_sales` — One Big Table

Table analytique centrale dénormalisée. Grain : **1 ligne = 1 transaction de vente**.

Contient toutes les dimensions (produit, famille, magasin, pays, prix, promotion) et les mesures associées.

#### Champs principaux

| Catégorie | Champs |
|---|---|
| Transaction | `transaction_id`, `transaction_date`, `transaction_day`, `transaction_month` |
| Produit | `product_id`, `product_code`, `product_name`, `brand`, `model` |
| Famille | `product_family_id`, `product_family_code`, `product_family_name` |
| Magasin | `store_id`, `store_code`, `store_name`, `city`, `region` |
| Géographie | `country_id`, `country_code`, `country_name` |
| Prix | `price_id`, `price_amount`, `currency_code`, `price_scope`, `price_type` |
| Classification | `is_store_specific_price`, `is_promotional_price`, `is_price_temporally_valid` |
| Performance prix | `unit_price`, `price_difference`, `price_difference_rate` |
| Promotion | `promotion_id`, `promotion_code`, `has_promotion`, `is_promotion_temporally_valid` |
| Mesures | `quantity`, `revenue` |
| Flags | `is_promo` |

---

### 5.2 `kpi_price_performance` — KPI Performance Prix

Modèle de KPI basé sur une comparaison glissante de 30 jours et un benchmark pays.

#### Grain

**1 ligne = 1 combinaison (country_id, store_id, product_id)**

#### Périodes d'analyse

| Période | Définition |
|---|---|
| Période courante | `max_date - 30 jours` → `max_date` |
| Période précédente | `max_date - 60 jours` → `max_date - 30 jours` |

#### Métriques calculées

| Champ | Description |
|---|---|
| `current_revenue` / `previous_revenue` | CA sur chaque période |
| `revenue_change_pct` | Variation de CA en % |
| `current_quantity` / `previous_quantity` | Quantités vendues par période |
| `quantity_change_pct` | Variation de quantité en % |
| `current_avg_selling_price` | Prix moyen de vente (période courante) |
| `previous_avg_selling_price` | Prix moyen de vente (période précédente) |
| `avg_price_change_pct` | Variation du prix moyen en % |
| `country_avg_selling_price` | Prix moyen pays pour le même produit |
| `price_vs_country_benchmark_pct` | Écart du prix magasin vs benchmark pays (%) |
| `current_promo_revenue_share` | Part du CA sous promotion (%) |

#### Flags métier

| Flag | Valeurs | Logique |
|---|---|---|
| `performance_flag` | `NEW_ACTIVITY`, `STRONG_GROWTH`, `STRONG_DECLINE`, `STABLE`, `NOT_COMPARABLE` | Basé sur `revenue_change_pct` (seuil ±20%) |
| `benchmark_flag` | `ABOVE_COUNTRY_BENCHMARK`, `BELOW_COUNTRY_BENCHMARK`, `ALIGNED_WITH_COUNTRY_BENCHMARK`, `NOT_COMPARABLE` | Comparaison prix moyen magasin vs prix moyen pays |

#### Règles des flags

**performance_flag :**
- `NEW_ACTIVITY` — pas de CA précédent mais CA courant > 0
- `STRONG_GROWTH` — variation CA ≥ +20%
- `STRONG_DECLINE` — variation CA ≤ -20%
- `STABLE` — variation CA entre -20% et +20%
- `NOT_COMPARABLE` — aucune condition remplie

**benchmark_flag :**
- `ALIGNED_WITH_COUNTRY_BENCHMARK` — prix moyen magasin = prix moyen pays (arrondi à 2 décimales)
- `ABOVE_COUNTRY_BENCHMARK` — prix moyen magasin > prix moyen pays
- `BELOW_COUNTRY_BENCHMARK` — prix moyen magasin < prix moyen pays
- `NOT_COMPARABLE` — données insuffisantes (prix null)

---

### 5.3 `kpi_promo_performance` — KPI Performance Promotionnelle

Modèle de KPI mesurant l'efficacité des promotions par comparaison produit AVANT vs PENDANT la promo.

> **Règle métier** : L'uplift principal est calculé **uniquement au niveau produit** (même produit avant vs pendant promo). La famille n'est **jamais** utilisée pour calculer l'uplift principal.

#### Grain

**1 ligne = 1 combinaison (country_id, store_id, product_id, promotion_id)**

#### Périodes d'analyse

| Période | Définition |
|---|---|
| Période promo | `promotion_start_date` → `promotion_end_date` |
| Période baseline | `promotion_start_date - 14 jours` → `promotion_start_date - 1 jour` |

#### KPI principal — Uplift produit

| Champ | Description |
|---|---|
| `promo_quantity` / `promo_revenue` | Ventes du produit pendant la promo |
| `baseline_quantity` / `baseline_revenue` | Ventes du **même produit** avant la promo (14j) |
| `promo_daily_quantity` / `promo_daily_revenue` | Moyenne journalière pendant la promo |
| `baseline_daily_quantity` / `baseline_daily_revenue` | Moyenne journalière avant la promo |
| `quantity_uplift_rate` | Taux d'accélération quantité (décimal) |
| `quantity_uplift_pct` | Accélération quantité en % |
| `additional_quantity` | Volume incrémental attribuable à la promo |
| `revenue_uplift_rate` | Taux d'accélération CA (décimal) |
| `revenue_uplift_pct` | Accélération CA en % |
| `additional_revenue` | CA incrémental attribuable à la promo |
| `avg_price_discount_effect_pct` | Variation du prix moyen de vente (%) |

#### KPI complémentaire — Effet famille (cannibalisation / halo)

| Champ | Description |
|---|---|
| `family_promo_quantity` / `family_promo_revenue` | Ventes des **autres produits** de la même famille pendant la promo |
| `family_baseline_quantity` / `family_baseline_revenue` | Ventes des autres produits de la famille avant la promo |
| `family_quantity_variation_pct` | Variation quantité famille (%) |
| `family_revenue_variation_pct` | Variation CA famille (%) |
| `family_effect_flag` | Indicateur d'effet famille |

#### Flags métier

**promo_performance_flag :**
- `EFFICIENT_PROMO` — uplift quantité > 0 ET uplift CA > 0
- `VOLUME_ONLY_PROMO` — uplift quantité > 0 mais uplift CA ≤ 0
- `UNDERPERFORMING_PROMO` — uplift quantité ≤ 0 ET uplift CA < 0
- `MIXED_PERFORMANCE` — autres combinaisons
- `NOT_COMPARABLE` — baseline à 0 (pas de données avant promo)

**family_effect_flag :**
- `CANNIBALIZATION` — variation quantité famille < -10%
- `HALO_EFFECT` — variation quantité famille > +10%
- `NEUTRAL` — variation entre -10% et +10%
- `NO_FAMILY_DATA` — pas de données famille disponibles