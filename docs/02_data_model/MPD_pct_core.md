# PDM — PostgreSQL Physical Schema `pct_core`

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

```sql
CREATE TABLE pct_core.user_account (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);
```

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

---

### 3.9 sales_transaction

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
    CONSTRAINT chk_sales_transaction_unit_price_non_negative
        CHECK (unit_price >= 0),
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

---

### Default Values

* `active` → TRUE
* `currency_code` → 'EUR'
* `created_at` → CURRENT_TIMESTAMP
* `display_order` → 0

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
* Add price change workflow
* Add price change audit trail

---

## 7. Conclusion

This PDM faithfully reflects the PostgreSQL implementation of the business model.

It provides:

* a robust foundation for the backend
* a base for future evolutions
* a key validation element for the certification
