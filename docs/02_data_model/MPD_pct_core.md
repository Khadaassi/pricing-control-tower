# MPD — Schéma physique PostgreSQL `pct_core`

## 1. Objectif

Ce modèle physique de données (MPD) décrit l’implémentation concrète du schéma `pct_core` dans PostgreSQL.

Il précise :

* les types SQL
* les contraintes (PK, FK, UNIQUE)
* les valeurs par défaut
* les règles d’intégrité

Ce modèle est directement issu des migrations Alembic et représente l’état réel de la base.

---

## 2. Schéma

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

## 4. Contraintes et règles d’intégrité

### Clés primaires

Toutes les tables utilisent une clé primaire de type :

```sql
INTEGER GENERATED ALWAYS AS IDENTITY
```

---

### Contraintes d’unicité

* `country.code`
* `store.code`
* `product_family.code`
* `product.code`
* `promotion.code`
* `user_account.email`

---

### Clés étrangères

Les relations sont assurées par des contraintes FK explicites :

* store → country
* product → product_family
* product_image → product
* promotion → product
* promotion → country
* promotion → store
* promotion → user_account
* price → product, country, store, promotion, user_account

---

### Valeurs par défaut

* `active` → TRUE
* `currency_code` → 'EUR'
* `created_at` → CURRENT_TIMESTAMP
* `display_order` → 0

---

## 5. Règles métier implicites

### Scope des prix

* `price_scope = 'COUNTRY'` → prix au niveau pays
* `price_scope = 'STORE'` → prix spécifique magasin

### Cohérence attendue

* un `store` appartient toujours à un `country`
* un `price` de type STORE doit référencer un `store`
* un `price` de type COUNTRY doit référencer un `country`

Ces règles sont actuellement gérées au niveau applicatif.

---

## 6. Évolutions prévues

* ajout de contraintes CHECK (cohérence `price_scope`)
* gestion des chevauchements de périodes de prix
* ajout d’index pour performance
* création du schéma analytique `pct_analytics`

---

## 7. Conclusion

Le MPD reflète fidèlement l’implémentation PostgreSQL du modèle métier.

Il constitue :

* une base robuste pour le backend
* un socle pour les évolutions futures
* un élément clé de validation pour la certification
