# API Design — Pricing Control Tower

## Overview

This API provides access to pricing, product and promotion data.

The endpoints are designed for:

* business users (pricing analysis)
* frontend consumption
* future analytical use cases

---

# 1. GET /products

## Business purpose

Retrieve the list of products available in the system.

Used for:

* product browsing
* pricing analysis
* frontend display

---

## Query parameters

| Parameter         | Type    | Description                     |
| ----------------- | ------- | ------------------------------- |
| active            | boolean | Filter active/inactive products |
| product_family_id | integer | Filter by product family        |
| code              | string  | Retrieve a specific product     |

---

## Response structure

```json
[
  {
    "id": 1,
    "code": "SKU-001",
    "name": "Product name",
    "description": "Description",
    "brand": "Brand",
    "model": "Model",
    "active": true,
    "family": {
      "id": 10,
      "code": "FAM-001",
      "name": "Camping"
    }
  }
]
```

---

# 2. GET /prices

## Business purpose

Retrieve pricing data defined at country or store level.

Used for:

* price analysis
* promotion tracking
* anomaly detection

---

## Query parameters

| Parameter   | Type    | Description       |
| ----------- | ------- | ----------------- |
| product_id  | integer | Filter by product |
| country_id  | integer | Filter by country |
| store_id    | integer | Filter by store   |
| price_scope | string  | COUNTRY or STORE  |
| price_type  | string  | STANDARD or PROMO |
| status      | string  | Price status      |

---

## Response structure

```json
[
  {
    "id": 1,
    "product_id": 10,
    "product_code": "SKU-001",
    "product_name": "Product name",
    "price_scope": "COUNTRY",
    "country_id": 1,
    "store_id": null,
    "price_type": "STANDARD",
    "amount": 99.99,
    "currency_code": "EUR",
    "effective_from": "2026-01-01",
    "effective_to": null,
    "status": "ACTIVE",
    "promotion_id": null
  }
]
```

---

# 3. GET /promotions

## Business purpose

Retrieve promotions defined in the system.

Each promotion targets a single product and applies a discount of type `PERCENTAGE` or `FIXED_PRICE`.

Promotions can be scoped at:

* country level
* store level

---

## Query parameters

| Parameter     | Type    | Description                                      |
| ------------- | ------- | ------------------------------------------------ |
| country_id    | integer | Filter by country                                |
| store_id      | integer | Filter by store                                  |
| active        | boolean | Filter active promotions                         |
| discount_type | string  | Promotion type (`PERCENTAGE` or `FIXED_PRICE`)   |
| product_id    | integer | Filter by product                                |

---

## Response structure

```json
[
  {
    "id": 1,
    "code": "PROMO-001",
    "name": "Winter Sale",
    "description": "Discount",
    "discount_type": "PERCENTAGE",
    "discount_value": 20.00,
    "product_id": 1,
    "start_date": "2026-01-01",
    "end_date": "2026-01-31",
    "country_id": 1,
    "store_id": null,
    "active": true
  }
]
```

---

# 4. GET /sales (Sprint 3)

## Business purpose

Retrieve raw sales transaction records with optional filters.

Used for:

* sales exploration and filtering
* promotion impact verification
* data quality checks

---

## Query parameters

| Parameter    | Type    | Description                               |
| ------------ | ------- | ----------------------------------------- |
| product_id   | integer | Filter by product                         |
| store_id     | integer | Filter by store                           |
| promotion_id | integer | Filter by promotion                       |
| is_promo     | boolean | Filter promotional / non-promo sales      |
| price_type   | string  | STANDARD or PROMO                         |
| limit        | integer | Max records returned (1–500, default 100) |

---

## Response structure

```json
[
  {
    "transaction_id": 1,
    "transaction_date": "2026-03-15T14:30:00",
    "product_id": 31,
    "store_id": 5,
    "price_id": 12,
    "promotion_id": 2,
    "quantity": 3,
    "unit_price": 49.99,
    "revenue": 149.97,
    "is_promo": true,
    "price_scope": "STORE",
    "price_type": "PROMO"
  }
]
```

---

# 5. GET /kpis (Sprint 3)

## Business purpose

Return aggregated MVP sales KPIs computed dynamically from `pct_analytics.obt_sales`.

Used for:

* dashboard summary cards
* promotional performance monitoring
* quick business health check

---

## Query parameters

| Parameter  | Type    | Description                          |
| ---------- | ------- | ------------------------------------ |
| product_id | integer | Filter by product                    |
| store_id   | integer | Filter by store                      |
| is_promo   | boolean | Filter promotional / non-promo sales |
| price_type | string  | STANDARD or PROMO                    |

---

## Response structure

```json
{
  "total_sales_count": 1250,
  "total_quantity": 3420,
  "total_revenue": 187530.00,
  "promo_sales_count": 320,
  "promo_revenue": 45200.00,
  "promo_sales_share": 0.2560,
  "average_order_value": 150.02
}
```

---

## KPI definitions

| KPI                 | Calculation                                 |
| ------------------- | ------------------------------------------- |
| total_sales_count   | Count of transactions                       |
| total_quantity      | Sum of quantities sold                      |
| total_revenue       | Sum of revenue                              |
| promo_sales_count   | Count of transactions where is_promo = true |
| promo_revenue       | Revenue from promotional sales              |
| promo_sales_share   | promo_sales_count / total_sales_count       |
| average_order_value | total_revenue / total_sales_count           |

---

# 6. GET /anomalies (Sprint 3)

## Business purpose

Detect rule-based business anomalies from the analytical model.

MVP rule: flag promotions whose total revenue is **below a configurable threshold** (default: 500 €). This helps pricing managers identify underperforming promotions.

---

## Query parameters

| Parameter    | Type    | Description                                      |
| ------------ | ------- | ------------------------------------------------ |
| min_revenue  | decimal | Revenue threshold for detection (default 500.00) |
| promotion_id | integer | Filter by promotion                              |
| product_id   | integer | Filter by product                                |
| store_id     | integer | Filter by store                                  |
| limit        | integer | Max anomalies returned (1–200, default 50)       |

---

## Response structure

```json
[
  {
    "anomaly_type": "LOW_PROMOTION_REVENUE",
    "severity": "HIGH",
    "message": "Promotion 2 generated revenue below the configured threshold.",
    "promotion_id": 2,
    "product_id": 31,
    "store_id": null,
    "sales_count": 4,
    "total_quantity": 7,
    "total_revenue": 120.50,
    "threshold": 500.00
  }
]
```

---

## Severity logic

| Condition                     | Severity |
| ----------------------------- | -------- |
| revenue < 50 % of threshold  | HIGH     |
| revenue < 80 % of threshold  | MEDIUM   |
| revenue < 100 % of threshold | LOW      |

---

# 7. POST /price-change-requests

## Business purpose

Create a new price change request to initiate a pricing workflow.

---

## Request body

```json
{
  "product_id": 1,
  "price_id": 10,
  "requested_by_user_id": 1,
  "new_amount": 89.99,
  "reason": "Align price with competitor"
}
```

---

## Response structure

```json
{
  "id": 1,
  "product_id": 1,
  "price_id": 10,
  "requested_by_user_id": 1,
  "new_amount": 89.99,
  "reason": "Align price with competitor",
  "status": "PENDING",
  "created_at": "2026-05-01T10:00:00Z",
  "approved_at": null,
  "rejection_reason": null,
  "rejected_by_user_id": null,
  "rejected_at": null
}
```

---

# 8. GET /price-change-requests

## Business purpose

List all price change requests with optional filters.

---

## Query parameters

| Parameter | Type   | Description                            |
| --------- | ------ | -------------------------------------- |
| status    | string | Filter by status (PENDING, APPROVED, REJECTED) |

---

## Response structure

```json
[
  {
    "id": 1,
    "product_id": 1,
    "price_id": 10,
    "requested_by_user_id": 1,
    "new_amount": 89.99,
    "reason": "Align price with competitor",
    "status": "PENDING",
    "created_at": "2026-05-01T10:00:00Z",
    "approved_at": null,
    "rejection_reason": null,
    "rejected_by_user_id": null,
    "rejected_at": null
  }
]
```

---

# 9. POST /price-change-requests/{id}/approve

## Business purpose

Approve a pending price change request and apply the new price.

---

## Request body

```json
{
  "approved_by_user_id": 2
}
```

---

## Response structure

Returns the updated price change request with `status: "APPROVED"` and `approved_at` timestamp.

---

## Error cases

| HTTP Code | Condition                              |
| --------- | -------------------------------------- |
| 404       | Price change request not found         |
| 409       | Request is not in PENDING status       |
| 404       | approved_by_user_id does not exist     |

---


# 11. GET /price-history

## Business purpose

Retrieve the history of price changes for audit and traceability.

---

## Query parameters

| Parameter           | Type    | Description                |
| ------------------- | ------- | -------------------------- |
| price_change_request_id | int | Filter by request id       |
| previous_price_id   | int     | Filter by previous price   |
| new_price_id        | int     | Filter by new price        |
| applied_by_user_id  | int     | Filter by user             |
| ...                 | ...     | ...                        |

---

## Response structure

```json
[
  {
    "id": 1,
    "price_change_request_id": 42,
    "previous_price_id": 10,
    "new_price_id": 11,
    "old_price_amount": 99.99,
    "new_price_amount": 89.99,
    "applied_by_user_id": 2,
    "applied_at": "2026-05-06T10:00:00Z",
    "created_at": "2026-05-06T10:00:00Z"
  }
]
```

---

# Changelog

## Sprint 5 (feature/expose_analytics)

- Added `GET /analytics/sales` — enriched OBT rows from `pct_analytics.obt_sales` with product/store/country/is_promo/limit filters
- Added `GET /analytics/sales/summary` — per-product aggregated KPIs (revenue, quantity, promo share, period)
- New Django pages:
  - `AnalyticsSalesView` → `/analytique/ventes/` — filterable analytics table
  - `ProductAnalyticsView` → `/produits/<id>/analytique/` — JSON endpoint for product sidebar KPIs
- Anomalies page redesigned: card grid with right-panel detail + actions (create price request, view analytics)

## Sprint 4

- The PriceHistoryRead schema was aligned with other models:
    - Field `history_id` renamed to `id`.
    - Only database fields are exposed (removed product_id, country_id, store_id from schema).
    - Added docstring for clarity and maintainability.

## Business purpose

Reject a pending price change request with a mandatory reason.

Used for:

* pricing governance
* documenting why a request was denied
* maintaining audit trail

---

## Request body

```json
{
  "rejected_by_user_id": 2,
  "reason": "Price reduction too aggressive for current margin targets"
}
```

---

## Validation rules

| Field               | Rule                              |
| ------------------- | --------------------------------- |
| rejected_by_user_id | Must be > 0, must exist in system |
| reason              | Must not be empty after trimming  |

---

## Response structure

```json
{
  "id": 1,
  "product_id": 1,
  "price_id": 10,
  "requested_by_user_id": 1,
  "new_amount": 89.99,
  "reason": "Align price with competitor",
  "status": "REJECTED",
  "created_at": "2026-05-01T10:00:00Z",
  "approved_at": null,
  "rejection_reason": "Price reduction too aggressive for current margin targets",
  "rejected_by_user_id": 2,
  "rejected_at": "2026-05-02T09:15:00Z"
}
```

---

## Error cases

| HTTP Code | Condition                              |
| --------- | -------------------------------------- |
| 404       | Price change request not found         |
| 409       | Request is not in PENDING status       |
| 404       | rejected_by_user_id does not exist     |
| 400       | Reason is empty or blank               |

---

## Side effects

* Status updated to `REJECTED`
* `rejection_reason`, `rejected_by_user_id`, `rejected_at` populated
* Audit log entry created with `action_type = REQUEST_REJECTED`

---

# 12. GET /analytics/sales

## Business purpose

Return enriched OBT rows directly from `pct_analytics.obt_sales`.

Used for:

* Ventes Analytiques page (full transaction detail with dbt enrichment)
* Exploring price performance, promo classification, and geography in one place

---

## Query parameters

| Parameter  | Type    | Description                               |
| ---------- | ------- | ----------------------------------------- |
| product_id | integer | Filter by product                         |
| store_id   | integer | Filter by store                           |
| country_id | integer | Filter by country                         |
| is_promo   | boolean | Filter promotional / non-promo sales      |
| limit      | integer | Max records returned (1–1000, default 100)|

---

## Response structure

```json
[
  {
    "transaction_id": 1,
    "transaction_day": "2026-03-15",
    "product_code": "SKU-001",
    "product_name": "VTT Trail Pro",
    "brand": "Trek",
    "product_family_name": "Vélos",
    "store_name": "Paris Nord",
    "city": "Paris",
    "country_name": "France",
    "price_scope": "STORE",
    "price_type": "PROMO",
    "currency_code": "EUR",
    "price_amount": "799.00",
    "unit_price": "639.20",
    "price_difference_rate": "-20.0%",
    "quantity": 2,
    "revenue": "1278.40",
    "is_promo": true,
    "promotion_name": "Summer Sale",
    "discount_type": "PERCENTAGE",
    "discount_value": 20.0
  }
]
```

---

# 13. GET /analytics/sales/summary

## Business purpose

Return aggregated KPIs for a single product from `pct_analytics.obt_sales`.

Used for:

* Product detail sidebar — "Performances analytiques" section
* Quick overview of a product's sales history without full row access

---

## Query parameters

| Parameter  | Type    | Description              |
| ---------- | ------- | ------------------------ |
| product_id | integer | **Required.** Product ID |

---

## Response structure

```json
{
  "product_id": 31,
  "transaction_count": 142,
  "total_quantity": 387,
  "total_revenue": 45320.80,
  "avg_selling_price": 319.16,
  "promo_transactions": 58,
  "promo_revenue": 16200.40,
  "promo_share_pct": 40.8,
  "first_sale_date": "2025-11-01",
  "last_sale_date": "2026-04-30"
}
```

---

## KPI definitions

| KPI               | Calculation                                         |
| ----------------- | --------------------------------------------------- |
| transaction_count | COUNT(*) on obt_sales for this product              |
| total_quantity    | SUM(quantity)                                       |
| total_revenue     | SUM(revenue)                                        |
| avg_selling_price | AVG(unit_price)                                     |
| promo_transactions| COUNT(*) WHERE is_promo = true                      |
| promo_revenue     | SUM(revenue) WHERE is_promo = true                  |
| promo_share_pct   | promo_transactions / transaction_count × 100        |
| first/last_sale   | MIN/MAX(transaction_day)                            |

---

# Design principles

* Simple REST endpoints
* Read-oriented API for MVP
* Business-aligned data exposure
* Analytical calculations isolated in service files
* No complex business logic directly inside route handlers

---

# Next evolutions

* Add filters and pagination improvements
* Add authentication and roles
* Add AI assistant integration
