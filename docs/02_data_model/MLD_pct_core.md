# LDM — Transactional Schema `pct_core`

## 1. Purpose

This logical data model (LDM) describes the table structure of the `pct_core` schema, used to manage transactional data for the Pricing Control Tower application.

It enables:

* structuring business entities
* guaranteeing relationship consistency
* preparing the PostgreSQL and SQLAlchemy implementation
* ensuring operation traceability

---

## 2. Schema Overview

The `pct_core` schema contains the following tables:

* country
* store
* product_family
* product
* product_image
* user_account
* promotion
* price
* price_history (planned)
* price_change_request (planned)
* audit_log (planned)
* sales_transaction

---

## 3. Tables

### 3.1 country

| Field | Type         | Constraints      |
| ----- | ------------ | ---------------- |
| id    | INTEGER      | PK               |
| code  | VARCHAR(10)  | UNIQUE, NOT NULL |
| name  | VARCHAR(100) | NOT NULL         |

---

### 3.2 store

| Field        | Type         | Constraints                |
| ------------ | ------------ | -------------------------- |
| id           | INTEGER      | PK                         |
| code         | VARCHAR(20)  | UNIQUE, NOT NULL           |
| name         | VARCHAR(100) | NOT NULL                   |
| country_id   | INTEGER      | FK → country(id), NOT NULL |
| city         | VARCHAR(100) | NULL                       |
| region       | VARCHAR(255) | NULL                       |
| opening_date | DATE         | NULL                       |

---

### 3.3 product_family

| Field       | Type         | Constraints      |
| ----------- | ------------ | ---------------- |
| id          | INTEGER      | PK               |
| code        | VARCHAR(50)  | UNIQUE, NOT NULL |
| name        | VARCHAR(100) | NOT NULL         |
| description | TEXT         | NULL             |

---

### 3.4 product

| Field             | Type         | Constraints                       |
| ----------------- | ------------ | --------------------------------- |
| id                | INTEGER      | PK                                |
| code              | VARCHAR(50)  | UNIQUE, NOT NULL                  |
| name              | VARCHAR(150) | NOT NULL                          |
| description       | TEXT         | NULL                              |
| brand             | VARCHAR(100) | NULL                              |
| model             | VARCHAR(100) | NULL                              |
| active            | BOOLEAN      | NOT NULL, DEFAULT TRUE            |
| product_family_id | INTEGER      | FK → product_family(id), NOT NULL |

---

### 3.5 product_image

| Field         | Type         | Constraints                |
| ------------- | ------------ | -------------------------- |
| id            | INTEGER      | PK                         |
| product_id    | INTEGER      | FK → product(id), NOT NULL |
| image_url     | VARCHAR(500) | NOT NULL                   |
| alt_text      | VARCHAR(255) | NULL                       |
| display_order | INTEGER      | NOT NULL, DEFAULT 0        |

---

### 3.6 user_account

| Field     | Type         | Constraints            |
| --------- | ------------ | ---------------------- |
| id        | INTEGER      | PK                     |
| email     | VARCHAR(255) | UNIQUE, NOT NULL       |
| full_name | VARCHAR(150) | NOT NULL               |
| active    | BOOLEAN      | NOT NULL, DEFAULT TRUE |

---

### 3.7 promotion

| Field          | Type          | Constraints                              |
| -------------- | ------------- | ---------------------------------------- |
| id             | INTEGER       | PK                                       |
| code           | VARCHAR(50)   | UNIQUE, NOT NULL                         |
| name           | VARCHAR(150)  | NOT NULL                                 |
| description    | TEXT          | NULL                                     |
| discount_type  | VARCHAR(20)   | NOT NULL, CHECK IN ('PERCENTAGE', 'FIXED_PRICE') |
| discount_value | NUMERIC(10,2) | NOT NULL                                 |
| product_id     | INTEGER       | FK → product(id), NOT NULL               |
| start_date     | DATE          | NOT NULL                                 |
| end_date       | DATE          | NOT NULL                                 |
| country_id     | INTEGER       | FK → country(id), NOT NULL               |
| store_id       | INTEGER       | FK → store(id), NULL                     |
| created_by     | INTEGER       | FK → user_account(id), NOT NULL          |
| created_at     | TIMESTAMP     | NOT NULL                                 |
| active         | BOOLEAN       | NOT NULL                                 |

---

### 3.8 price

| Field          | Type          | Constraints                     |
| -------------- | ------------- | ------------------------------- |
| id             | INTEGER       | PK                              |
| product_id     | INTEGER       | FK → product(id), NOT NULL      |
| price_scope    | VARCHAR(20)   | NOT NULL                        |
| country_id     | INTEGER       | FK → country(id), NOT NULL      |
| store_id       | INTEGER       | FK → store(id), NULL            |
| price_type     | VARCHAR(20)   | NOT NULL                        |
| amount         | NUMERIC(10,2) | NOT NULL                        |
| currency_code  | VARCHAR(3)    | NOT NULL                        |
| effective_from | DATE          | NOT NULL                        |
| effective_to   | DATE          | NULL                            |
| status         | VARCHAR(20)   | NOT NULL                        |
| promotion_id   | INTEGER       | FK → promotion(id), NULL        |
| reason         | TEXT          | NULL                            |
| created_by     | INTEGER       | FK → user_account(id), NOT NULL |
| created_at     | TIMESTAMP     | NOT NULL                        |

---

### 3.9 sales_transaction

| Field            | Type          | Constraints                     |
| ---------------- | ------------- | ------------------------------- |
| transaction_id   | BIGINT        | PK                              |
| transaction_date | TIMESTAMP     | NOT NULL                        |
| product_id       | INTEGER       | FK → product(id), NOT NULL      |
| store_id         | INTEGER       | FK → store(id), NOT NULL        |
| price_id         | INTEGER       | FK → price(id), NOT NULL        |
| promotion_id     | INTEGER       | FK → promotion(id), NULL        |
| quantity         | INTEGER       | NOT NULL, CHECK > 0             |
| unit_price       | NUMERIC(10,2) | NOT NULL, CHECK >= 0            |
| revenue          | NUMERIC(12,2) | NOT NULL, CHECK >= 0            |
| is_promo         | BOOLEAN       | NOT NULL                        |
| price_scope      | VARCHAR(20)   | NOT NULL                        |
| price_type       | VARCHAR(20)   | NOT NULL                        |

---

## 4. Main Business Rules

### Price Scope

* `price_scope = COUNTRY` → price defined at country level
* `price_scope = STORE` → price defined at store level

### Identifier Consistency

* `store_id` always implies a consistent `country_id`
* a product always belongs to a family

### Temporality

* a price is valid over a period (`effective_from`, `effective_to`)
* a promotion is active over a period (`start_date`, `end_date`)

### Traceability

* every price or promotion creation is associated with a user
* `created_by` and `created_at` fields enable auditing

---

## 5. Evolution Points

* Add business constraints (date consistency, non-overlapping prices)
* Add tables:

  * `price_history`
  * `price_change_request`
  * `audit_log`
* Advanced status management (`status`)
* Application-level business rule validation

---

## 6. Conclusion

This LDM provides a solid foundation for:

* backend development (FastAPI)
* migration management (Alembic)
* building the analytical layer (`pct_analytics`)

It reflects a balance between:

* simplicity (MVP)
* business consistency
* extensibility
