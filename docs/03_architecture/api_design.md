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

# Design principles

* Simple REST endpoints
* Read-oriented API for MVP
* Business-aligned data exposure
* Analytical calculations isolated in service files
* No complex business logic directly inside route handlers

---

# Next evolutions

* Add filters and pagination improvements
* Add write endpoints (price changes)
* Add authentication and roles
* Add AI assistant integration
