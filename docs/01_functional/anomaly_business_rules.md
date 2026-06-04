# Anomaly Business Rules

This document describes the four pricing anomaly detection rules exposed by the `GET /anomalies` endpoint. Each rule produces anomalies with a type identifier, a severity level, and a plain-French explanation message designed to be readable by pricing managers and AI assistants.

---

## Common Response Fields

| Field                | Type             | Description                                                  |
| -------------------- | ---------------- | ------------------------------------------------------------ |
| `anomaly_type`       | string           | Rule identifier (see below)                                  |
| `severity`           | `LOW/MEDIUM/HIGH`| Severity level                                               |
| `message`            | string           | Business explanation in plain French                         |
| `product_id`         | integer          | Product concerned                                            |
| `product_family_name`| string or null   | Product family name                                          |
| `store_id`           | integer or null  | Store concerned (null = national scope)                      |
| `promotion_id`       | integer or null  | Promotion concerned (null for price-based rules)             |
| `promotion_active`   | boolean          | Whether the promotion is still active                        |
| `total_revenue`      | decimal          | Actual value (promo revenue or store price depending on rule)|
| `threshold`          | decimal          | Expected value (expected revenue or reference price)         |

---

## Rule 1 — UNDERPERFORMING_PROMO

**What it detects:** A promotion whose daily revenue during the promotional period is lower than the daily revenue of the same product in the 14 days before the promotion started.

**Data source:** `pct_analytics.kpi_promo_performance` (dbt mart)

**Entry criterion:** `revenue_uplift_rate < -10 %`
(The promotion generates less daily revenue than the pre-promotion baseline.)

**Exclusion:** Products without a pre-promotion baseline (`NOT_COMPARABLE` flag) are excluded. They are handled by INEFFECTIVE_DISCOUNT instead.

**Cannibalization effect:** If the product family's overall revenue also dropped during the promotion (`family_effect_flag = CANNIBALIZATION`), severity is escalated by one level.

| Condition                                           | Severity |
| --------------------------------------------------- | -------- |
| uplift between -10 % and -50 %                      | LOW      |
| uplift ≤ -50 %, or negative uplift + cannibalization| MEDIUM   |
| uplift ≤ -80 %, or uplift ≤ -50 % + cannibalization| HIGH     |

**Business interpretation:** The promotion is not only failing to generate additional sales — it is actively reducing revenue compared to the period without promotion. This may indicate a poorly targeted discount, a substitution effect, or an error in the promotional setup.

---

## Rule 2 — INEFFECTIVE_DISCOUNT

**What it detects:** A promotion with a significant effective discount (price dropped by ≥ 20 %) that generated no volume uplift. The margin is sacrificed without attracting more customers.

**Data source:** `pct_analytics.kpi_promo_performance`

**Entry criteria:**
- `avg_price_discount_effect_pct ≤ -20 %` (effective price reduction ≥ 20 %)
- `quantity_uplift_rate ≤ 0` (volume did not increase), OR `promo_performance_flag = NOT_COMPARABLE` (new product)

**Special case — new products:** If the product has no pre-promotion history (`NOT_COMPARABLE`), the rule still fires when the effective discount exceeds 50 %, as this likely indicates a data-entry error.

| Condition                       | Severity |
| ------------------------------- | -------- |
| effective discount 20 % – 30 %  | LOW      |
| effective discount 30 % – 50 %  | MEDIUM   |
| effective discount ≥ 50 %       | HIGH     |

**Business interpretation:** The promotion is costing the business margin without generating additional sales volume. The discount is not incentivizing purchases, which may indicate the wrong product was chosen, the discount level is insufficient to change buying behaviour, or the promotion conflicts with other factors (low stock, poor placement, etc.).

---

## Rule 3 — PRICE_ABOVE_REFERENCE

**What it detects:** An active store-level standard price that exceeds the national reference price for the same product.

**Data source:** `pct_core.price`

**Comparison:**
- Store price: `price_scope = STORE`, `price_type = STANDARD`, `status = ACTIVE`
- Reference price: `price_scope = COUNTRY`, `price_type = STANDARD`, `status = ACTIVE`
- Same `product_id` and `country_id`

**Entry criterion:** `store_price > reference_price × 1.05` (store price is more than 5 % above reference)

| Condition                      | Severity |
| ------------------------------ | -------- |
| 5 % – 15 % above reference     | LOW      |
| 15 % – 30 % above reference    | MEDIUM   |
| ≥ 30 % above reference         | HIGH     |

**Business interpretation:** The store is selling a product at a higher price than the nationally defined catalog price. This damages price consistency across the network, may violate pricing contracts, and risks customer complaints if the discrepancy is noticed. Typical causes: manual override not validated, outdated local price not refreshed after a national price change.

**Note:** This rule only fires when store-level price overrides exist in `pct_core.price` with `price_scope = STORE`. It returns no anomalies if all prices are set at country level.

---

## Rule 4 — INTER_STORE_PRICE_GAP

**What it detects:** A store whose active standard price for a product deviates abnormally from the average price of the same product across all stores in the same country.

**Data source:** `pct_core.price`

**Computation:** For each product with at least 2 active store-level standard prices, the national store average is computed. Any store whose price deviates by more than 15 % from that average is flagged.

**Entry criterion:** `|store_price − national_avg| / national_avg > 15 %`

**Minimum stores required:** 2 (to compute a meaningful average)

| Condition              | Severity |
| ---------------------- | -------- |
| 15 % – 25 % deviation  | LOW      |
| 25 % – 40 % deviation  | MEDIUM   |
| ≥ 40 % deviation       | HIGH     |

**Business interpretation:** This store's price is significantly inconsistent with prices charged at other stores for the same product. This may create customer inequity, arbitrage risk (customers travelling to cheaper stores), or indicate a pricing error. Both over- and under-pricing are flagged; the `message` field specifies whether the price is above or below the average.

**Note:** Like rule 3, this rule only fires when store-level price overrides are present in `pct_core.price`.

---

## Negative Margin — Not Implemented (Out of Scope)

Detection of negative margin cases (`selling_price < unit_cost`) is **not implemented** because the current data model does not include a `unit_cost` field in any available table. If cost data is added to the schema in a future sprint, a `NEGATIVE_MARGIN` rule can be added following the same pattern as the rules above.

---

## API Usage

```
GET /anomalies
```

| Parameter    | Type    | Description                              |
| ------------ | ------- | ---------------------------------------- |
| promotion_id | integer | Filter by promotion (rules 1 & 2 only)   |
| product_id   | integer | Filter by product                        |
| store_id     | integer | Filter by store                          |
| limit        | integer | Max results (1–200, default 20)          |
| offset       | integer | Pagination offset (default 0)            |

The response includes anomalies from all four rules combined, sorted by detection order within each rule (most severe first). Use the `anomaly_type` field to distinguish rules client-side or in AI assistant prompts.
