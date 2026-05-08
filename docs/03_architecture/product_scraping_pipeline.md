# Product Scraping and Ingestion Pipeline Documentation

## Objective

This document describes the product scraping and ingestion pipeline implemented during Sprint 6 of the Pricing Control Tower project.

The goal of this pipeline is to collect external product catalog data, transform it into a structure compatible with the `pct_core` PostgreSQL schema, and insert it into the business database in a controlled and traceable way.

The pipeline follows this flow:

```text
FitnessBoutique website
→ Scrapy extraction
→ Raw JSON
→ Business transformation
→ Processed JSON files
→ PostgreSQL insertion
→ Manual validation
````

---

## 1. Target Website

The selected source is FitnessBoutique France:

```text
https://www.fitnessboutique.fr
```

FitnessBoutique is an e-commerce website selling fitness and sport equipment.

The MVP focuses only on sport equipment and accessories. Nutrition, supplements, customer accounts, checkout pages and protected content are excluded from the scraping scope.

---

## 2. Scraped Collections

The scraping pipeline targets the following product collections:

| Category code             | Category name              | Collection path                                            |
| ------------------------- | -------------------------- | ---------------------------------------------------------- |
| `MUSCULATION_ACCESSORY`   | Accessoires de musculation | `/collections/musculation-accessoire`                      |
| `FITNESS_ACCESSORY`       | Accessoires fitness        | `/collections/accessoires-fitness`                         |
| `DUMBBELL_BAR`            | Haltères et barres         | `/collections/haltere`                                     |
| `DUMBBELL_SPECIFIC`       | Haltères spécifiques       | `/collections/poid-haltere-barres-et-halteres-specifiques` |
| `WEIGHT_BENCH`            | Bancs de musculation       | `/collections/banc-musculation`                            |
| `WEIGHT_BENCH_SIMPLE`     | Bancs de musculation seuls | `/collections/banc-musculation-seul`                       |
| `TREADMILL`               | Tapis de course            | `/collections/tapis-de-course`                             |
| `EXERCISE_BIKE`           | Vélos d’appartement        | `/collections/velo-appartement`                            |
| `ROWING_MACHINE`          | Rameurs                    | `/collections/rameur`                                      |
| `MAGNETIC_ROWING_MACHINE` | Rameurs magnétiques        | `/collections/rameur-magnetique`                           |

---

## 3. Scraping Implementation

The Scrapy project is located in:

```text
data/scraping/
```

The main spider is:

```text
data/scraping/product_catalog/spiders/fitnessboutique_spider.py
```

The spider extracts product cards from collection pages using the validated HTML selector:

```python
response.css("product-card")
```

Pagination is handled automatically by detecting links containing:

```python
a[href*='page=']
```

The spider follows collection pages until no next page is found.

---

## 4. Scraped Fields

The raw JSON file is generated at:

```text
data/raw/fitnessboutique_products.json
```

Each raw product row contains the following fields:

| Field                 | Description                                        |
| --------------------- | -------------------------------------------------- |
| `source`              | Source website identifier                          |
| `collection_url`      | Root collection URL                                |
| `scraped_page_url`    | Actual page URL scraped                            |
| `category_code`       | Internal category code derived from the collection |
| `category_name`       | Internal category name derived from the collection |
| `external_product_id` | Product ID from the source website                 |
| `product_url`         | Product detail URL                                 |
| `brand`               | Product brand                                      |
| `name`                | Product name                                       |
| `description`         | Short product description when available           |
| `price_text`          | Raw displayed price                                |
| `original_price_text` | Previous price when available                      |
| `availability_text`   | Displayed availability text                        |
| `inventory_level`     | Source inventory status                            |
| `image_url`           | Main product image URL                             |
| `image_alt`           | Image alternative text when available              |

---

## 5. Raw Data Volume

The current raw scraping output contains:

```text
Raw rows: 652
Unique product URLs: 606
Duplicate raw product groups: 46
Product categories: 10
Missing required fields: 0
```

Duplicates exist because some products appear in several FitnessBoutique collections.

At the raw layer, duplicates are intentionally preserved to reflect the source website structure.

---

## 6. Transformation Layer

The transformation script is located at:

```text
data/transformation/transform_scraped_products.py
```

It reads:

```text
data/raw/fitnessboutique_products.json
```

and generates four processed files:

```text
data/processed/product_families.json
data/processed/products.json
data/processed/product_images.json
data/processed/prices.json
```

The transformation step performs:

* validation of required raw fields;
* deduplication of products using `product_url`;
* selection of one main product family per product;
* price parsing from French price format to decimal format;
* preparation of database-compatible JSON files.

---

## 7. Deduplication Rule

The raw file may contain the same product in multiple collections.

For the business model, one product is identified by one unique `product_url`.

The transformation keeps one business product per `product_url`.

Observed result:

```text
Raw rows: 652
Unique transformed products: 606
Duplicate raw product groups: 46
```

---

## 8. Product Family Selection Rule

The `pct_core.product` table supports one `product_family_id` per product.

When a product appears in several source collections, the transformation selects the most specific product family using the following priority order:

```text
MAGNETIC_ROWING_MACHINE
ROWING_MACHINE
TREADMILL
EXERCISE_BIKE
WEIGHT_BENCH_SIMPLE
WEIGHT_BENCH
DUMBBELL_SPECIFIC
DUMBBELL_BAR
MUSCULATION_ACCESSORY
FITNESS_ACCESSORY
```

This rule is documented to ensure deterministic and explainable mapping.

---

## 9. Mapping to PostgreSQL Tables

### `product_family`

| Processed field | PostgreSQL column                     |
| --------------- | ------------------------------------- |
| `code`          | `pct_core.product_family.code`        |
| `name`          | `pct_core.product_family.name`        |
| `description`   | `pct_core.product_family.description` |

### `product`

| Processed field       | PostgreSQL column                                |
| --------------------- | ------------------------------------------------ |
| `code`                | `pct_core.product.code`                          |
| `name`                | `pct_core.product.name`                          |
| `description`         | `pct_core.product.description`                   |
| `brand`               | `pct_core.product.brand`                         |
| `model`               | `pct_core.product.model`                         |
| `active`              | `pct_core.product.active`                        |
| `product_family_code` | resolved to `pct_core.product.product_family_id` |

### `product_image`

| Processed field | PostgreSQL column                               |
| --------------- | ----------------------------------------------- |
| `product_code`  | resolved to `pct_core.product_image.product_id` |
| `image_url`     | `pct_core.product_image.image_url`              |
| `alt_text`      | `pct_core.product_image.alt_text`               |
| `display_order` | `pct_core.product_image.display_order`          |

### `price`

| Processed field      | PostgreSQL column                       |
| -------------------- | --------------------------------------- |
| `product_code`       | resolved to `pct_core.price.product_id` |
| `country_code`       | resolved to `pct_core.price.country_id` |
| `price_scope`        | `pct_core.price.price_scope`            |
| `price_type`         | `pct_core.price.price_type`             |
| `amount`             | `pct_core.price.amount`                 |
| `currency_code`      | `pct_core.price.currency_code`          |
| `effective_from`     | `pct_core.price.effective_from`         |
| `effective_to`       | `pct_core.price.effective_to`           |
| `status`             | `pct_core.price.status`                 |
| `promotion_id`       | `pct_core.price.promotion_id`           |
| `reason`             | `pct_core.price.reason`                 |
| `created_by_user_id` | `pct_core.price.created_by`             |

---

## 10. Insertion Order

The insertion order respects PostgreSQL foreign key constraints:

```text
1. product_family
2. product
3. product_image
4. price
```

Insertion scripts are located in:

```text
data/insertion/
```

Scripts:

```text
load_product_families.py
load_products.py
load_product_images.py
load_prices.py
```

---

## 11. Default Values

The following default values are used for MVP compatibility:

| Field                | Value        |
| -------------------- | ------------ |
| `country_code`       | `FR`         |
| `price_scope`        | `COUNTRY`    |
| `price_type`         | `STANDARD`   |
| `currency_code`      | `EUR`        |
| `effective_from`     | `2026-05-08` |
| `effective_to`       | `null`       |
| `status`             | `ACTIVE`     |
| `promotion_id`       | `null`       |
| `created_by_user_id` | `1`          |

The database contains the required reference values:

```text
country: FR
user_account: id 1, admin@pct.local
```

---

## 12. MVP Choices

The MVP keeps the ingestion pipeline simple and controlled.

Included:

* product families;
* products;
* main product images;
* initial country standard prices;
* source traceability through raw and processed files.

Excluded:

* product variants;
* multiple images per product;
* store-level prices;
* promotions;
* stock quantities;
* customer data;
* checkout data;
* protected or authenticated pages.

---

## 13. Scraping Limitations

The pipeline depends on the HTML structure of the target website. If the website changes its product card structure, selectors may need to be updated.

Known limitations:

* no JavaScript rendering engine is used;
* only data available in static HTML is extracted;
* only selected collections are scraped;
* only the main image is retained;
* duplicates are handled during transformation, not during raw scraping;
* the pipeline is not designed for high-frequency scraping.

The scraping is performed for educational purposes, with limited scope and conservative request settings.

---

## 14. Validation Evidence

The pipeline was manually validated with the following checks:

```text
Raw rows: 652
Unique product URLs: 606
Missing required fields: 0
Product families: 10
Products: 606
Product images: 606
Prices: 606
```

Database validations include:

* product families inserted without duplicate codes;
* products linked to valid product families;
* product images linked to valid products;
* prices linked to valid products and country;
* standard country prices respecting business constraints.

---

## 15. Defensibility for Certification Review

This pipeline is defensible for the certification review because it demonstrates:

* external data collection with Scrapy;
* raw data persistence in JSON;
* transformation into business-compatible structures;
* controlled insertion into PostgreSQL;
* respect of foreign key constraints;
* explicit MVP limitations;
* reproducible scripts;
* traceable intermediate files;
* manual validation evidence.

````

