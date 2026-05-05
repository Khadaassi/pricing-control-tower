# LDM — Analytical Schema `pct_analytics`

## 1. Purpose

This logical data model describes the structure of the `pct_analytics` schema, built by dbt from transactional data in the `pct_core` schema.

It serves as a reference for:

* understanding the analytical layer of the project
* documenting dbt models (staging → intermediate → marts)
* guiding KPI interpretation

---

## 2. dbt Model Architecture

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

## 3. Staging Layer

Staging models extract and rename columns from the `pct_core` source tables.

| Model | Source | Description |
|---|---|---|
| `stg_sales` | `pct_core.sales_transaction` | Raw sales transactions |
| `stg_product` | `pct_core.product` | Product reference |
| `stg_product_family` | `pct_core.product_family` | Product families |
| `stg_store` | `pct_core.store` | Store reference |
| `stg_country` | `pct_core.country` | Country reference |
| `stg_price` | `pct_core.price` | Price reference |
| `stg_promotion` | `pct_core.promotion` | Promotion reference |

---

## 4. Intermediate Layer

### 4.1 `int_sales_enriched`

Joins sales with product, store, price, and promotion dimensions.

| Field | Description |
|---|---|
| `transaction_id` | PK — unique sale identifier |
| `transaction_date` | Transaction date and time |
| `product_id`, `product_code`, `product_name` | Product dimensions |
| `brand`, `model`, `product_family_id` | Product attributes |
| `store_id`, `store_code`, `store_name` | Store dimensions |
| `country_id`, `city`, `region` | Geographic dimensions |
| `price_id`, `price_amount`, `currency_code` | Reference price |
| `price_effective_from`, `price_effective_to` | Price validity period |
| `price_scope` | `COUNTRY` or `STORE` |
| `price_type` | `STANDARD` or `PROMO` |
| `is_store_specific_price` | Boolean — store-specific price |
| `is_promotional_price` | Boolean — promotional price |
| `is_price_temporally_valid` | Boolean — temporal price validity |
| `price_difference` | Gap between paid price and reference price |
| `price_difference_rate` | Paid price vs reference price deviation rate |
| `promotion_id`, `promotion_code`, `promotion_name` | Promotion dimensions |
| `discount_type`, `discount_value` | Discount type and value |
| `promotion_start_date`, `promotion_end_date` | Promotion period |
| `quantity`, `unit_price`, `revenue` | Transaction measures |
| `is_promo` | Boolean — transaction linked to a promotion |

---

## 5. Marts Layer

### 5.1 `obt_sales` — One Big Table

Central denormalized analytical table. Grain: **1 row = 1 sales transaction**.

Contains all dimensions (product, family, store, country, price, promotion) and associated measures.

#### Main Fields

| Category | Fields |
|---|---|
| Transaction | `transaction_id`, `transaction_date`, `transaction_day`, `transaction_month` |
| Product | `product_id`, `product_code`, `product_name`, `brand`, `model` |
| Family | `product_family_id`, `product_family_code`, `product_family_name` |
| Store | `store_id`, `store_code`, `store_name`, `city`, `region` |
| Geography | `country_id`, `country_code`, `country_name` |
| Price | `price_id`, `price_amount`, `currency_code`, `price_scope`, `price_type` |
| Classification | `is_store_specific_price`, `is_promotional_price`, `is_price_temporally_valid` |
| Price Performance | `unit_price`, `price_difference`, `price_difference_rate` |
| Promotion | `promotion_id`, `promotion_code`, `has_promotion`, `is_promotion_temporally_valid` |
| Measures | `quantity`, `revenue` |
| Flags | `is_promo` |

---

### 5.2 `kpi_price_performance` — Price Performance KPI

KPI model based on a 30-day rolling comparison and a country benchmark.

#### Grain

**1 row = 1 combination (country_id, store_id, product_id)**

#### Analysis Periods

| Period | Definition |
|---|---|
| Current period | `max_date - 30 days` → `max_date` |
| Previous period | `max_date - 60 days` → `max_date - 30 days` |

#### Computed Metrics

| Field | Description |
|---|---|
| `current_revenue` / `previous_revenue` | Revenue for each period |
| `revenue_change_pct` | Revenue change (%) |
| `current_quantity` / `previous_quantity` | Quantities sold per period |
| `quantity_change_pct` | Quantity change (%) |
| `current_avg_selling_price` | Average selling price (current period) |
| `previous_avg_selling_price` | Average selling price (previous period) |
| `avg_price_change_pct` | Average price change (%) |
| `country_avg_selling_price` | Country average price for the same product |
| `price_vs_country_benchmark_pct` | Store price vs country benchmark deviation (%) |
| `current_promo_revenue_share` | Revenue share under promotion (%) |

#### Business Flags

| Flag | Values | Logic |
|---|---|---|
| `performance_flag` | `NEW_ACTIVITY`, `STRONG_GROWTH`, `STRONG_DECLINE`, `STABLE`, `NOT_COMPARABLE` | Based on `revenue_change_pct` (threshold ±20%) |
| `benchmark_flag` | `ABOVE_COUNTRY_BENCHMARK`, `BELOW_COUNTRY_BENCHMARK`, `ALIGNED_WITH_COUNTRY_BENCHMARK`, `NOT_COMPARABLE` | Store avg price vs country avg price comparison |

#### Flag Rules

**performance_flag:**
- `NEW_ACTIVITY` — no previous revenue but current revenue > 0
- `STRONG_GROWTH` — revenue change ≥ +20%
- `STRONG_DECLINE` — revenue change ≤ -20%
- `STABLE` — revenue change between -20% and +20%
- `NOT_COMPARABLE` — no condition met

**benchmark_flag:**
- `ALIGNED_WITH_COUNTRY_BENCHMARK` — store avg price = country avg price (rounded to 2 decimals)
- `ABOVE_COUNTRY_BENCHMARK` — store avg price > country avg price
- `BELOW_COUNTRY_BENCHMARK` — store avg price < country avg price
- `NOT_COMPARABLE` — insufficient data (null price)

---

### 5.3 `kpi_promo_performance` — Promotional Performance KPI

KPI model measuring promotion effectiveness by comparing product sales BEFORE vs DURING the promo.

> **Business rule**: The main uplift is calculated **only at product level** (same product before vs during promo). Family is **never** used to calculate the main uplift.

#### Grain

**1 row = 1 combination (country_id, store_id, product_id, promotion_id)**

#### Analysis Periods

| Period | Definition |
|---|---|
| Promo period | `promotion_start_date` → `promotion_end_date` |
| Baseline period | `promotion_start_date - 14 days` → `promotion_start_date - 1 day` |

#### Main KPI — Product Uplift

| Field | Description |
|---|---|
| `promo_quantity` / `promo_revenue` | Product sales during the promotion |
| `baseline_quantity` / `baseline_revenue` | Sales of the **same product** before the promotion (14d) |
| `promo_daily_quantity` / `promo_daily_revenue` | Daily average during the promotion |
| `baseline_daily_quantity` / `baseline_daily_revenue` | Daily average before the promotion |
| `quantity_uplift_rate` | Quantity acceleration rate (decimal) |
| `quantity_uplift_pct` | Quantity acceleration (%) |
| `additional_quantity` | Incremental volume attributable to the promotion |
| `revenue_uplift_rate` | Revenue acceleration rate (decimal) |
| `revenue_uplift_pct` | Revenue acceleration (%) |
| `additional_revenue` | Incremental revenue attributable to the promotion |
| `avg_price_discount_effect_pct` | Average selling price change (%) |

#### Complementary KPI — Family Effect (Cannibalization / Halo)

| Field | Description |
|---|---|
| `family_promo_quantity` / `family_promo_revenue` | Sales of **other products** in the same family during the promotion |
| `family_baseline_quantity` / `family_baseline_revenue` | Sales of other family products before the promotion |
| `family_quantity_variation_pct` | Family quantity change (%) |
| `family_revenue_variation_pct` | Family revenue change (%) |
| `family_effect_flag` | Family effect indicator |

#### Business Flags

**promo_performance_flag:**
- `EFFICIENT_PROMO` — quantity uplift > 0 AND revenue uplift > 0
- `VOLUME_ONLY_PROMO` — quantity uplift > 0 but revenue uplift ≤ 0
- `UNDERPERFORMING_PROMO` — quantity uplift ≤ 0 AND revenue uplift < 0
- `MIXED_PERFORMANCE` — other combinations
- `NOT_COMPARABLE` — baseline at 0 (no data before promo)

**family_effect_flag:**
- `CANNIBALIZATION` — family quantity change < -10%
- `HALO_EFFECT` — family quantity change > +10%
- `NEUTRAL` — change between -10% and +10%
- `NO_FAMILY_DATA` — no family data available
