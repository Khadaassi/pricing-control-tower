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

Promotions can be applied at:

* country level
* store level

---

## Query parameters

| Parameter     | Type    | Description              |
| ------------- | ------- | ------------------------ |
| country_id    | integer | Filter by country        |
| store_id      | integer | Filter by store          |
| active        | boolean | Filter active promotions |
| discount_type | string  | Promotion type           |

---

## Response structure

```json
[
  {
    "id": 1,
    "code": "PROMO-001",
    "name": "Winter Sale",
    "description": "Discount",
    "discount_type": "PERCENT",
    "discount_value": 20.00,
    "start_date": "2026-01-01",
    "end_date": "2026-01-31",
    "country_id": 1,
    "store_id": null,
    "active": true
  }
]
```

---

# Design principles

* Simple REST endpoints
* Read-oriented API for MVP
* Business-aligned data exposure
* No business logic duplication (handled in database)

---

# Next evolutions

* Add filters and pagination improvements
* Add write endpoints (price changes)
* Add authentication and roles
* Add AI assistant integration
