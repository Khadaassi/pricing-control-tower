# Sprint 2 — Manual API Tests

## Objective

Validate the correct behavior of all API endpoints implemented during Sprint 2.

---

## Environment

* Backend: FastAPI (local)
* Database: PostgreSQL (Docker)
* Base URL: http://127.0.0.1:8000

---

# 1. GET /health

## Purpose

Check that the API is running.

## Request

curl http://127.0.0.1:8000/health

## Expected Result

* HTTP 200
* Response confirms API is up

## Observed Result

* Status: 200 OK
* Response: {"status": "ok"}

## Status

PASS

---

# 2. GET /products

## Purpose

Retrieve all products.

## Request

curl http://127.0.0.1:8000/products

## Expected Result

* List of products
* Each product contains family information

## Observed Result

* Products returned correctly
* Family data present

## Status

PASS

---

## Filter Test — active products

## Request

curl "http://127.0.0.1:8000/products?active=true"

## Expected Result

* Only active products

## Observed Result

* Filter applied correctly

## Status

PASS

---

# 3. GET /prices

## Purpose

Retrieve pricing data.

## Request

curl http://127.0.0.1:8000/prices

## Expected Result

* List of prices
* Includes product info
* Includes scope and type

## Observed Result

* Prices returned correctly
* product_code and product_name visible
* price_scope and price_type correct

## Status

PASS

---

## Filter Test — country

## Request

curl "http://127.0.0.1:8000/prices?country_id=1"

## Expected Result

* Only prices for country_id=1

## Observed Result

* Filter applied correctly

## Status

PASS

---

## Filter Test — price type

## Request

curl "http://127.0.0.1:8000/prices?price_type=PROMO"

## Expected Result

* Only promotional prices

## Observed Result

* Correct results returned

## Status

PASS

---

# 4. GET /promotions

## Purpose

Retrieve promotions.

## Request

curl http://127.0.0.1:8000/promotions

## Expected Result

* List of promotions
* Includes country/store logic

## Observed Result

* Promotions returned correctly
* country_id always present
* store_id nullable

## Status

PASS

---

## Filter Test — country

## Request

curl "http://127.0.0.1:8000/promotions?country_id=1"

## Expected Result

* Only promotions for country_id=1

## Observed Result

* Filter applied correctly

## Status

PASS

---

## Filter Test — store

## Request

curl "http://127.0.0.1:8000/promotions?store_id=10"

## Expected Result

* No promotions returned for a non-existing store_id

## Observed Result

* Empty list returned: []

## Status

PASS

---

## Filter Test — active promotions

## Request

curl "http://127.0.0.1:8000/promotions?active=true"

## Expected Result

* Only active promotions

## Observed Result

* Filter works as expected

## Status

PASS

---

# Conclusion

All endpoints implemented in Sprint 2:

* respond without errors
* return consistent and usable data
* support filtering as expected

The API is considered stable and ready for further development.
