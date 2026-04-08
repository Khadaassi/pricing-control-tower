# MLP — Schéma transactionnel `pct_core`

## 1. Objectif

Ce modèle logique de données (MLP) décrit la structure des tables du schéma `pct_core`, utilisé pour gérer les données transactionnelles de l’application Pricing Control Tower.

Il permet de :

* structurer les entités métier
* garantir la cohérence des relations
* préparer l’implémentation PostgreSQL et SQLAlchemy
* assurer la traçabilité des opérations

---

## 2. Schéma global

Le schéma `pct_core` regroupe les tables suivantes :

* country
* store
* product_family
* product
* product_image
* user_account
* promotion
* price
* price_history (à venir)
* price_change_request (à venir)
* audit_log (à venir)
* sales_transaction (à venir)

---

## 3. Tables

### 3.1 country

| Champ | Type         | Contraintes      |
| ----- | ------------ | ---------------- |
| id    | INTEGER      | PK               |
| code  | VARCHAR(10)  | UNIQUE, NOT NULL |
| name  | VARCHAR(100) | NOT NULL         |

---

### 3.2 store

| Champ        | Type         | Contraintes                |
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

| Champ       | Type         | Contraintes      |
| ----------- | ------------ | ---------------- |
| id          | INTEGER      | PK               |
| code        | VARCHAR(50)  | UNIQUE, NOT NULL |
| name        | VARCHAR(100) | NOT NULL         |
| description | TEXT         | NULL             |

---

### 3.4 product

| Champ             | Type         | Contraintes                       |
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

| Champ         | Type         | Contraintes                |
| ------------- | ------------ | -------------------------- |
| id            | INTEGER      | PK                         |
| product_id    | INTEGER      | FK → product(id), NOT NULL |
| image_url     | VARCHAR(500) | NOT NULL                   |
| alt_text      | VARCHAR(255) | NULL                       |
| display_order | INTEGER      | NOT NULL, DEFAULT 0        |

---

### 3.6 user_account

| Champ     | Type         | Contraintes            |
| --------- | ------------ | ---------------------- |
| id        | INTEGER      | PK                     |
| email     | VARCHAR(255) | UNIQUE, NOT NULL       |
| full_name | VARCHAR(150) | NOT NULL               |
| active    | BOOLEAN      | NOT NULL, DEFAULT TRUE |

---

### 3.7 promotion

| Champ          | Type          | Contraintes                     |
| -------------- | ------------- | ------------------------------- |
| id             | INTEGER       | PK                              |
| code           | VARCHAR(50)   | UNIQUE, NOT NULL                |
| name           | VARCHAR(150)  | NOT NULL                        |
| description    | TEXT          | NULL                            |
| discount_type  | VARCHAR(20)   | NOT NULL                        |
| discount_value | NUMERIC(10,2) | NOT NULL                        |
| start_date     | DATE          | NOT NULL                        |
| end_date       | DATE          | NOT NULL                        |
| store_id       | INTEGER       | FK → store(id), NOT NULL        |
| created_by     | INTEGER       | FK → user_account(id), NOT NULL |
| created_at     | TIMESTAMP     | NOT NULL                        |
| active         | BOOLEAN       | NOT NULL                        |

---

### 3.8 price

| Champ          | Type          | Contraintes                     |
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

## 4. Règles métier principales

### Portée des prix

* `price_scope = COUNTRY` → prix défini au niveau pays
* `price_scope = STORE` → prix défini au niveau magasin

### Cohérence des identifiants

* `store_id` implique toujours un `country_id` cohérent
* un produit appartient obligatoirement à une famille

### Temporalité

* un prix est valide sur une période (`effective_from`, `effective_to`)
* une promotion est active sur une période (`start_date`, `end_date`)

### Traçabilité

* toute création de prix ou promotion est associée à un utilisateur
* les champs `created_by` et `created_at` permettent l’audit

---

## 5. Points d’évolution

* ajout de contraintes métier (cohérence des dates, non-chevauchement des prix)
* ajout des tables :

  * `price_history`
  * `price_change_request`
  * `audit_log`
  * `sales_transaction`
* gestion avancée des statuts (`status`)
* validation applicative des règles métier

---

## 6. Conclusion

Ce MLP constitue une base solide pour :

* le développement backend (FastAPI)
* la gestion des migrations (Alembic)
* la construction de la couche analytique (`pct_analytics`)

Il reflète un équilibre entre :

* simplicité (MVP)
* cohérence métier
* évolutivité
