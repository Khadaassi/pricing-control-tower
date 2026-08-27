# PDM — PostgreSQL Physical Schema `pct_core`

_Last verified: 2026-08-24_

## 1. Purpose

This physical data model (PDM) describes the concrete implementation of the `pct_core` schema in PostgreSQL.

It specifies:

* SQL types
* Constraints (PK, FK, UNIQUE)
* Default values
* Integrity rules

This model is directly derived from Alembic migrations and represents the actual state of the database.

---

## 2. Schema

```sql
CREATE SCHEMA IF NOT EXISTS pct_core;
```

---

## 3. Tables

### 3.1 country

```sql
CREATE TABLE pct_core.country (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL
);
```

---

### 3.2 store

```sql
CREATE TABLE pct_core.store (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    country_id INTEGER NOT NULL,
    city VARCHAR(100),
    region VARCHAR(255),
    opening_date DATE,
    CONSTRAINT fk_store_country
        FOREIGN KEY (country_id)
        REFERENCES pct_core.country(id)
);
```

---

### 3.3 product_family

```sql
CREATE TABLE pct_core.product_family (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT
);
```

---

### 3.4 product

```sql
CREATE TABLE pct_core.product (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    brand VARCHAR(100),
    model VARCHAR(100),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    product_family_id INTEGER NOT NULL,
    CONSTRAINT fk_product_family
        FOREIGN KEY (product_family_id)
        REFERENCES pct_core.product_family(id)
);
```

---

### 3.5 product_image

```sql
CREATE TABLE pct_core.product_image (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id INTEGER NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    alt_text VARCHAR(255),
    display_order INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT fk_product_image_product
        FOREIGN KEY (product_id)
        REFERENCES pct_core.product(id)
);
```

---

### 3.6 user_account

> ⚠️ **Obsolete (verified 2026-08-24)** — This `CREATE TABLE` no longer reflects the actual state: the table also carries `country_id`, `store_id` and a `ck_user_account_scope` constraint. It also carried a `role` column (VARCHAR(50), CHECK IN 4 values) between migrations `f984259217d9` (2026-05-31) and `5672c0a352d1` (2026-06-01), never reflected in this document and since removed. Current state below, based on `backend/app/models/user_account.py` and migration `5672c0a352d1`.

```sql
CREATE TABLE pct_core.user_account (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    country_id INTEGER,
    store_id INTEGER,
    CONSTRAINT fk_user_account_country
        FOREIGN KEY (country_id)
        REFERENCES pct_core.country(id),
    CONSTRAINT fk_user_account_store
        FOREIGN KEY (store_id)
        REFERENCES pct_core.store(id),
    CONSTRAINT ck_user_account_scope
        CHECK (store_id IS NULL OR country_id IS NOT NULL)
);
```

Migration `5672c0a352d1` is the head of the Alembic chain (`backend/alembic/versions/`): no later revision references it as `down_revision`. It is therefore part of the current versioned code. Its actual application on each deployed environment remains **to be verified**.

---

### 3.7 promotion

```sql
CREATE TABLE pct_core.promotion (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    discount_type VARCHAR(20) NOT NULL,
    discount_value NUMERIC(10,2) NOT NULL,
    product_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    country_id INTEGER NOT NULL,
    store_id INTEGER,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT ck_promotion_discount_type
        CHECK (discount_type IN ('PERCENTAGE', 'FIXED_PRICE')),
    CONSTRAINT fk_promotion_product
        FOREIGN KEY (product_id)
        REFERENCES pct_core.product(id),
    CONSTRAINT fk_promotion_country
        FOREIGN KEY (country_id)
        REFERENCES pct_core.country(id),
    CONSTRAINT fk_promotion_store
        FOREIGN KEY (store_id)
        REFERENCES pct_core.store(id),
    CONSTRAINT fk_promotion_user
        FOREIGN KEY (created_by)
        REFERENCES pct_core.user_account(id)
);
```

---

### 3.8 price

```sql
CREATE TABLE pct_core.price (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id INTEGER NOT NULL,
    price_scope VARCHAR(20) NOT NULL,
    country_id INTEGER NOT NULL,
    store_id INTEGER,
    price_type VARCHAR(20) NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    currency_code VARCHAR(3) NOT NULL DEFAULT 'EUR',
    effective_from DATE NOT NULL,
    effective_to DATE,
    status VARCHAR(20) NOT NULL,
    promotion_id INTEGER,
    reason TEXT,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_price_product
        FOREIGN KEY (product_id)
        REFERENCES pct_core.product(id),
    CONSTRAINT fk_price_country
        FOREIGN KEY (country_id)
        REFERENCES pct_core.country(id),
    CONSTRAINT fk_price_store
        FOREIGN KEY (store_id)
        REFERENCES pct_core.store(id),
    CONSTRAINT fk_price_promotion
        FOREIGN KEY (promotion_id)
        REFERENCES pct_core.promotion(id),
    CONSTRAINT fk_price_user
        FOREIGN KEY (created_by)
        REFERENCES pct_core.user_account(id)
);
```

> ⚠️ **Added (verified 2026-08-24)** — The following CHECK constraints actually exist on `pct_core.price` (migration `4a5403c31464`, "add price business constraints") but were not listed in this `CREATE TABLE`:
>
> ```sql
> ALTER TABLE pct_core.price
>     ADD CONSTRAINT ck_price_scope_values
>         CHECK (price_scope IN ('COUNTRY', 'STORE')),
>     ADD CONSTRAINT ck_price_type_values
>         CHECK (price_type IN ('STANDARD', 'PROMO')),
>     ADD CONSTRAINT ck_price_scope_consistency
>         CHECK (
>             (price_scope = 'COUNTRY' AND country_id IS NOT NULL AND store_id IS NULL)
>             OR (price_scope = 'STORE' AND country_id IS NOT NULL AND store_id IS NOT NULL)
>         ),
>     ADD CONSTRAINT ck_price_promotion_consistency
>         CHECK (
>             (price_type = 'PROMO' AND promotion_id IS NOT NULL)
>             OR (price_type = 'STANDARD' AND promotion_id IS NULL)
>         ),
>     ADD CONSTRAINT ck_price_effective_dates
>         CHECK (effective_to IS NULL OR effective_to >= effective_from);
> ```

---

### 3.9 sales_transaction

> ⚠️ **Obsolete (verified 2026-08-24)** — The `chk_sales_transaction_unit_price_non_negative` constraint (`CHECK (unit_price >= 0)`) shown below was removed and replaced by `chk_sales_transaction_unit_price_positive` (`CHECK (unit_price > 0)`) by migration `fec186f3ed43` ("update unit_price constraint to be strictly positive"). The constraint name and logic shown in the `CREATE TABLE` below have been corrected to reflect the current state; the old version is kept here for historical reference: `CONSTRAINT chk_sales_transaction_unit_price_non_negative CHECK (unit_price >= 0)`.

```sql
CREATE TABLE pct_core.sales_transaction (
    transaction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    transaction_date TIMESTAMP NOT NULL,
    product_id INTEGER NOT NULL,
    store_id INTEGER NOT NULL,
    price_id INTEGER NOT NULL,
    promotion_id INTEGER,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10,2) NOT NULL,
    revenue NUMERIC(12,2) NOT NULL,
    is_promo BOOLEAN NOT NULL,
    price_scope VARCHAR(20) NOT NULL,
    price_type VARCHAR(20) NOT NULL,
    CONSTRAINT fk_sales_transaction_product
        FOREIGN KEY (product_id) REFERENCES pct_core.product(id),
    CONSTRAINT fk_sales_transaction_store
        FOREIGN KEY (store_id) REFERENCES pct_core.store(id),
    CONSTRAINT fk_sales_transaction_price
        FOREIGN KEY (price_id) REFERENCES pct_core.price(id),
    CONSTRAINT fk_sales_transaction_promotion
        FOREIGN KEY (promotion_id) REFERENCES pct_core.promotion(id),
    CONSTRAINT chk_sales_transaction_quantity_positive
        CHECK (quantity > 0),
    CONSTRAINT chk_sales_transaction_unit_price_positive
        CHECK (unit_price > 0),
    CONSTRAINT chk_sales_transaction_revenue_non_negative
        CHECK (revenue >= 0),
    CONSTRAINT chk_sales_transaction_revenue_consistency
        CHECK (revenue = quantity * unit_price),
    CONSTRAINT chk_sales_transaction_promo_consistency
        CHECK (
            (is_promo = TRUE AND promotion_id IS NOT NULL)
            OR (is_promo = FALSE AND promotion_id IS NULL)
        ),
    CONSTRAINT chk_sales_transaction_price_scope
        CHECK (price_scope IN ('COUNTRY', 'STORE')),
    CONSTRAINT chk_sales_transaction_price_type
        CHECK (price_type IN ('STANDARD', 'PROMO'))
);

CREATE INDEX ix_sales_transaction_transaction_date
    ON pct_core.sales_transaction (transaction_date);
CREATE INDEX ix_sales_transaction_product_id
    ON pct_core.sales_transaction (product_id);
CREATE INDEX ix_sales_transaction_store_id
    ON pct_core.sales_transaction (store_id);
CREATE INDEX ix_sales_transaction_promotion_id
    ON pct_core.sales_transaction (promotion_id);
```

---

> ⚠️ **Added (verified 2026-08-24)** — Tables 3.10 to 3.16 below were not present in this document even though they actually exist in the database. Structure read directly from `backend/app/models/` and the listed Alembic migrations.

### 3.10 price_history

```sql
CREATE TABLE pct_core.price_history (
    history_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    price_change_request_id INTEGER NOT NULL UNIQUE,
    previous_price_id INTEGER NOT NULL,
    new_price_id INTEGER NOT NULL,
    old_price_amount NUMERIC(10,2) NOT NULL,
    new_price_amount NUMERIC(10,2) NOT NULL,
    applied_by_user_id INTEGER NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_price_history_price_change_request
        FOREIGN KEY (price_change_request_id) REFERENCES pct_core.price_change_request(id),
    CONSTRAINT fk_price_history_previous_price
        FOREIGN KEY (previous_price_id) REFERENCES pct_core.price(id),
    CONSTRAINT fk_price_history_new_price
        FOREIGN KEY (new_price_id) REFERENCES pct_core.price(id),
    CONSTRAINT fk_price_history_applied_by_user
        FOREIGN KEY (applied_by_user_id) REFERENCES pct_core.user_account(id)
);

CREATE INDEX ix_price_history_previous_price_id ON pct_core.price_history (previous_price_id);
CREATE INDEX ix_price_history_new_price_id ON pct_core.price_history (new_price_id);
CREATE INDEX ix_price_history_applied_by_user_id ON pct_core.price_history (applied_by_user_id);
```

Source : `backend/app/models/price_history.py`, migration `c37ba1f9a561`.

---

### 3.11 price_change_request

```sql
CREATE TABLE pct_core.price_change_request (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id INTEGER NOT NULL,
    country_id INTEGER NOT NULL,
    store_id INTEGER,
    current_price_id INTEGER NOT NULL,
    old_price_amount NUMERIC(10,2) NOT NULL,
    requested_price_amount NUMERIC(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    justification TEXT NOT NULL,
    requested_effective_date DATE NOT NULL,
    requested_by_user_id INTEGER NOT NULL,
    rejection_reason TEXT,
    rejected_by_user_id INTEGER,
    rejected_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_price_change_request_product
        FOREIGN KEY (product_id) REFERENCES pct_core.product(id),
    CONSTRAINT fk_price_change_request_country
        FOREIGN KEY (country_id) REFERENCES pct_core.country(id),
    CONSTRAINT fk_price_change_request_store
        FOREIGN KEY (store_id) REFERENCES pct_core.store(id),
    CONSTRAINT fk_price_change_request_current_price
        FOREIGN KEY (current_price_id) REFERENCES pct_core.price(id),
    CONSTRAINT fk_price_change_request_requested_by_user
        FOREIGN KEY (requested_by_user_id) REFERENCES pct_core.user_account(id),
    CONSTRAINT fk_price_change_request_rejected_by_user
        FOREIGN KEY (rejected_by_user_id) REFERENCES pct_core.user_account(id),
    CONSTRAINT ck_price_change_request_status
        CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'APPLIED', 'FAILED')),
    CONSTRAINT ck_price_change_request_old_price_positive
        CHECK (old_price_amount > 0),
    CONSTRAINT ck_price_change_request_requested_price_positive
        CHECK (requested_price_amount > 0),
    CONSTRAINT ck_price_change_request_justification_not_empty
        CHECK (length(trim(justification)) > 0)
);

CREATE INDEX ix_price_change_request_product_id ON pct_core.price_change_request (product_id);
CREATE INDEX ix_price_change_request_country_id ON pct_core.price_change_request (country_id);
CREATE INDEX ix_price_change_request_store_id ON pct_core.price_change_request (store_id);
CREATE INDEX ix_price_change_request_status ON pct_core.price_change_request (status);
```

Source : `backend/app/models/price_change_request.py`, migrations `68b888fcb0b3`, `069820c274a5`, `ce9a2d7a81b5`.

---

### 3.12 audit_log

```sql
CREATE TABLE pct_core.audit_log (
    audit_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    price_change_request_id INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    performed_by_user_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_audit_log_price_change_request
        FOREIGN KEY (price_change_request_id) REFERENCES pct_core.price_change_request(id),
    CONSTRAINT fk_audit_log_performed_by_user
        FOREIGN KEY (performed_by_user_id) REFERENCES pct_core.user_account(id)
);

CREATE INDEX ix_audit_log_price_change_request_id ON pct_core.audit_log (price_change_request_id);
CREATE INDEX ix_audit_log_action_type ON pct_core.audit_log (action_type);
CREATE INDEX ix_audit_log_performed_by_user_id ON pct_core.audit_log (performed_by_user_id);
CREATE INDEX ix_audit_log_created_at ON pct_core.audit_log (created_at);
```

Source : `backend/app/models/audit_log.py`, migration `63cb3004e2e5`.

---

### 3.13 role (RBAC)

```sql
CREATE TABLE pct_core.role (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(100) NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    CONSTRAINT uq_role_code UNIQUE (code)
);
```

Source : `backend/app/models/role.py`, migration `8d805af24af3`.

---

### 3.14 permission (RBAC)

```sql
CREATE TABLE pct_core.permission (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(100) NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    CONSTRAINT uq_permission_code UNIQUE (code)
);
```

Source : `backend/app/models/permission.py`, migration `8d805af24af3`.

---

### 3.15 user_role (RBAC — junction table)

```sql
CREATE TABLE pct_core.user_role (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    CONSTRAINT pk_user_role PRIMARY KEY (user_id, role_id),
    CONSTRAINT fk_user_role_user
        FOREIGN KEY (user_id) REFERENCES pct_core.user_account(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_role_role
        FOREIGN KEY (role_id) REFERENCES pct_core.role(id) ON DELETE CASCADE
);
```

Source : `backend/app/models/user_role.py`, migration `8d805af24af3`.

---

### 3.16 role_permission (RBAC — junction table)

```sql
CREATE TABLE pct_core.role_permission (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    CONSTRAINT pk_role_permission PRIMARY KEY (role_id, permission_id),
    CONSTRAINT fk_role_permission_role
        FOREIGN KEY (role_id) REFERENCES pct_core.role(id) ON DELETE CASCADE,
    CONSTRAINT fk_role_permission_permission
        FOREIGN KEY (permission_id) REFERENCES pct_core.permission(id) ON DELETE CASCADE
);
```

Source : `backend/app/models/role_permission.py`, migration `8d805af24af3`.

---

## 4. Constraints and Integrity Rules

### Primary Keys

All tables use a primary key of type:

```sql
INTEGER GENERATED ALWAYS AS IDENTITY
```

---

### Unique Constraints

* `country.code`
* `store.code`
* `product_family.code`
* `product.code`
* `promotion.code`
* `user_account.email`
* `role.code` — ⚠️ added (verified 2026-08-24), migration `8d805af24af3`
* `permission.code` — ⚠️ added (verified 2026-08-24), migration `8d805af24af3`
* `price_history.price_change_request_id` — ⚠️ added (verified 2026-08-24), migration `c37ba1f9a561`

---

### Foreign Keys

Relationships are enforced by explicit FK constraints:

* store → country
* product → product_family
* product_image → product
* promotion → product
* promotion → country
* promotion → store
* promotion → user_account
* price → product, country, store, promotion, user_account
* sales_transaction → product, store, price, promotion

> ⚠️ **Added (verified 2026-08-24)** — Additional relationships that actually exist in the database, absent from this list:
> * user_account → country, store
> * price_history → price_change_request, price (x2: previous/new), user_account
> * price_change_request → product, country, store, price, user_account (x2: requested_by/rejected_by)
> * audit_log → price_change_request, user_account
> * user_role → user_account, role (ON DELETE CASCADE)
> * role_permission → role, permission (ON DELETE CASCADE)

---

### Default Values

* `active` → TRUE
* `currency_code` → 'EUR'
* `created_at` → CURRENT_TIMESTAMP
* `display_order` → 0
* `price_change_request.status` → 'PENDING' — ⚠️ added (verified 2026-08-24), migration `68b888fcb0b3`

---

## 5. Implicit Business Rules

### Price Scope

* `price_scope = 'COUNTRY'` → country-level price
* `price_scope = 'STORE'` → store-specific price

### Expected Consistency

* a `store` always belongs to a `country`
* a `price` with scope `STORE` must reference a `store`
* a `price` with scope `COUNTRY` must not reference a `store`
* a promotional price must be linked to a promotion
* a standard price must not be linked to a promotion

These rules are enforced by database constraints added via Alembic.

---

## 6. Planned Evolutions

* Handle overlapping price periods
* Add additional indexes to optimize analytical queries
* ~~Add price change workflow~~

  > ⚠️ **Obsolete (verified 2026-08-24)** — Completed: see table `price_change_request` (3.11) with statuses `PENDING`/`APPROVED`/`REJECTED`/`APPLIED`/`FAILED`.
* ~~Add price change audit trail~~

  > ⚠️ **Obsolete (verified 2026-08-24)** — Completed: see tables `price_history` (3.10) and `audit_log` (3.12).

---

## 7. Conclusion

This PDM faithfully reflects the PostgreSQL implementation of the business model.

It provides:

* a robust foundation for the backend
* a base for future evolutions
* a key validation element for the certification
