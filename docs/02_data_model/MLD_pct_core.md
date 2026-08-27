# LDM — Transactional Schema `pct_core`

_Last verified: 2026-08-24_

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
* price_history
* price_change_request
* audit_log
* sales_transaction
* role
* permission
* user_role
* role_permission

> ⚠️ **Obsolete (verified 2026-08-24)** — `price_history`, `price_change_request` and `audit_log` were listed above as "(planned)". They actually exist in the schema: see models `backend/app/models/price_history.py`, `price_change_request.py`, `audit_log.py`, as well as Alembic migrations `c37ba1f9a561` (price_history), `68b888fcb0b3` + `069820c274a5` + `ce9a2d7a81b5` (price_change_request) and `63cb3004e2e5` (audit_log). Their detailed structure is added in section 3. `role`, `permission`, `user_role`, `role_permission` are tables added since then (RBAC) and absent from the previous version of this document — see `backend/app/models/role.py`, `permission.py`, `user_role.py`, `role_permission.py` and migration `8d805af24af3`.

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

| Field      | Type         | Constraints                |
| ---------- | ------------ | --------------------------- |
| id         | INTEGER      | PK                          |
| email      | VARCHAR(255) | UNIQUE, NOT NULL            |
| full_name  | VARCHAR(150) | NOT NULL                    |
| active     | BOOLEAN      | NOT NULL, DEFAULT TRUE      |
| country_id | INTEGER      | FK → country(id), NULL      |
| store_id   | INTEGER      | FK → store(id), NULL        |

> ⚠️ **Added (verified 2026-08-24)** — `country_id` and `store_id` were not documented here. They actually exist (`backend/app/models/user_account.py`, migration `f984259217d9`) and carry the user's geographic scope (constraint `ck_user_account_scope`: `store_id IS NULL OR country_id IS NOT NULL`, added by migration `5672c0a352d1`).
>
> A `role` column (VARCHAR(50)) had been added to this table by migration `f984259217d9` (2026-05-31) but **never appeared** in this version of the document. It has since been removed by migration `5672c0a352d1` (2026-06-01, "remove single role from user_account") in favor of the RBAC model `role` / `permission` / `user_role` / `role_permission` described in 3.13–3.16. This migration `5672c0a352d1` is the head of the current Alembic chain (no other revision references it as `down_revision`): it is therefore part of the versioned code and will be applied by any `alembic upgrade head`. Whether this migration has already been run on each deployed environment (staging/prod) remains **to be verified** outside the source code.

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

> ⚠️ **Added (verified 2026-08-24)** — Sections 3.10 to 3.16 below document tables that already existed in the database (see 3.9 above which listed them as "planned") or that have since been introduced by the RBAC model, but that were not described in this document. Structure read directly from `backend/app/models/` and the corresponding Alembic migrations.

### 3.10 price_history

| Field                    | Type                      | Constraints                                        |
| ------------------------ | ------------------------- | --------------------------------------------------- |
| history_id               | INTEGER                   | PK                                                   |
| price_change_request_id  | INTEGER                   | FK → price_change_request(id), UNIQUE, NOT NULL, indexed |
| previous_price_id        | INTEGER                   | FK → price(id), NOT NULL, indexed                    |
| new_price_id             | INTEGER                   | FK → price(id), NOT NULL, indexed                    |
| old_price_amount         | NUMERIC(10,2)             | NOT NULL                                             |
| new_price_amount         | NUMERIC(10,2)             | NOT NULL                                             |
| applied_by_user_id       | INTEGER                   | FK → user_account(id), NOT NULL, indexed             |
| applied_at               | TIMESTAMP WITH TIME ZONE  | NOT NULL, DEFAULT now()                              |
| created_at               | TIMESTAMP WITH TIME ZONE  | NOT NULL, DEFAULT now()                              |

Source : `backend/app/models/price_history.py`, migration `c37ba1f9a561`.

---

### 3.11 price_change_request

| Field                      | Type                      | Constraints                                             |
| --------------------------- | ------------------------- | -------------------------------------------------------- |
| id                          | INTEGER                   | PK (Identity)                                             |
| product_id                  | INTEGER                   | FK → product(id), NOT NULL, indexed                       |
| country_id                  | INTEGER                   | FK → country(id), NOT NULL, indexed                        |
| store_id                    | INTEGER                   | FK → store(id), NULL, indexed                              |
| current_price_id            | INTEGER                   | FK → price(id), NOT NULL                                   |
| old_price_amount            | NUMERIC(10,2)             | NOT NULL, CHECK > 0                                        |
| requested_price_amount      | NUMERIC(10,2)             | NOT NULL, CHECK > 0                                        |
| status                      | VARCHAR(20)                | NOT NULL, DEFAULT 'PENDING', indexed, CHECK IN ('PENDING', 'APPROVED', 'REJECTED', 'APPLIED', 'FAILED') |
| justification                | TEXT                       | NOT NULL, CHECK length(trim(justification)) > 0            |
| requested_effective_date    | DATE                       | NOT NULL                                                    |
| requested_by_user_id        | INTEGER                   | FK → user_account(id), NOT NULL                             |
| rejection_reason            | TEXT                       | NULL                                                        |
| rejected_by_user_id         | INTEGER                   | FK → user_account(id), NULL                                 |
| rejected_at                 | TIMESTAMP WITH TIME ZONE  | NULL                                                         |
| created_at                  | TIMESTAMP WITH TIME ZONE  | NOT NULL, DEFAULT now()                                     |
| updated_at                  | TIMESTAMP WITH TIME ZONE  | NOT NULL, DEFAULT now()                                     |

Source: `backend/app/models/price_change_request.py`, migrations `68b888fcb0b3` (creation), `069820c274a5` (status/amount constraints), `ce9a2d7a81b5` (rejection fields).

---

### 3.12 audit_log

| Field                    | Type                      | Constraints                                          |
| ------------------------- | ------------------------- | ------------------------------------------------------ |
| audit_id                  | INTEGER                   | PK                                                     |
| price_change_request_id   | INTEGER                   | FK → price_change_request(id), NOT NULL, indexed        |
| action_type                | VARCHAR(50)                | NOT NULL, indexed                                       |
| performed_by_user_id       | INTEGER                   | FK → user_account(id), NOT NULL, indexed                |
| description                 | TEXT                       | NOT NULL                                                |
| created_at                  | TIMESTAMP WITH TIME ZONE  | NOT NULL, DEFAULT now(), indexed                        |

Source : `backend/app/models/audit_log.py`, migration `63cb3004e2e5`.

---

### 3.13 role (RBAC)

| Field       | Type          | Constraints      |
| ----------- | ------------- | ---------------- |
| id          | INTEGER       | PK                |
| code        | VARCHAR(100)  | UNIQUE, NOT NULL  |
| name        | VARCHAR(150)  | NOT NULL          |
| description | TEXT          | NULL              |

Source : `backend/app/models/role.py`, migration `8d805af24af3`.

---

### 3.14 permission (RBAC)

| Field       | Type          | Constraints      |
| ----------- | ------------- | ---------------- |
| id          | INTEGER       | PK                |
| code        | VARCHAR(100)  | UNIQUE, NOT NULL  |
| name        | VARCHAR(150)  | NOT NULL          |
| description | TEXT          | NULL              |

Source : `backend/app/models/permission.py`, migration `8d805af24af3`.

---

### 3.15 user_role (RBAC — junction table)

| Field    | Type    | Constraints                                              |
| -------- | ------- | ---------------------------------------------------------- |
| user_id  | INTEGER | PK (composite), FK → user_account(id), ON DELETE CASCADE     |
| role_id  | INTEGER | PK (composite), FK → role(id), ON DELETE CASCADE              |

Source : `backend/app/models/user_role.py`, migration `8d805af24af3`.

---

### 3.16 role_permission (RBAC — junction table)

| Field          | Type    | Constraints                                                  |
| -------------- | ------- | --------------------------------------------------------------- |
| role_id        | INTEGER | PK (composite), FK → role(id), ON DELETE CASCADE                  |
| permission_id  | INTEGER | PK (composite), FK → permission(id), ON DELETE CASCADE             |

Source : `backend/app/models/role_permission.py`, migration `8d805af24af3`.

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

* Add business constraints (date consistency: done via `ck_price_effective_dates`, see MPD; non-overlapping prices: not enforced — still an open point)
* ~~Add tables: `price_history`, `price_change_request`, `audit_log`~~

  > ⚠️ **Obsolete (verified 2026-08-24)** — These three tables now exist (see sections 3.10–3.12). Evolution point completed.
* Advanced status management (`status`): implemented for `price_change_request` (`PENDING`, `APPROVED`, `REJECTED`, `APPLIED`, `FAILED`, see 3.11)
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
