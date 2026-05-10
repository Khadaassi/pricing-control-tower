# Scraping Transformation Mapping

## Objective

This document describes how raw scraped FitnessBoutique product data is transformed into processed datasets compatible with the `pct_core` PostgreSQL schema.

The transformation prepares data for the following business tables:

- `product_family`
- `product`
- `product_image`
- `price`

No database insertion is performed during this step.

## Input

Raw input file:

```text
data/raw/fitnessboutique_products.json
````

The raw file contains product rows extracted from multiple FitnessBoutique collections.

Current observed volume:

```text
Raw rows: 652
Unique product URLs: 606
Duplicate raw product groups: 46
Categories: 10
```

## Output files

```text
data/processed/product_families.json
data/processed/products.json
data/processed/product_images.json
data/processed/prices.json
```

## Deduplication rule

The raw file may contain the same product in several source collections.

For the business model, one product is identified by one unique `product_url`.

The transformation keeps one business product per `product_url`.

## Product family selection rule

The `pct_core.product` table supports only one `product_family_id`.

When a product appears in multiple source collections, the transformation selects the most specific family using this priority order:

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

## Mapping to product_family

| Processed field | Source field                 |
| --------------- | ---------------------------- |
| code            | category_code                |
| name            | category_name                |
| description     | Generated import description |

## Mapping to product

| Processed field     | Source field / Rule         |
| ------------------- | --------------------------- |
| code                | `FB_` + external_product_id |
| name                | name                        |
| description         | description                 |
| brand               | brand                       |
| model               | null                        |
| active              | true                        |
| product_family_code | selected category_code      |
| source              | source                      |
| external_product_id | external_product_id         |
| source_product_url  | product_url                 |

## Mapping to product_image

| Processed field | Source field / Rule         |
| --------------- | --------------------------- |
| product_code    | `FB_` + external_product_id |
| image_url       | image_url                   |
| alt_text        | image_alt                   |
| display_order   | 0                           |

## Mapping to price

| Processed field    | Source field / Rule                                                   |
| ------------------ | --------------------------------------------------------------------- |
| product_code       | `FB_` + external_product_id                                           |
| country_code       | FR                                                                    |
| price_scope        | COUNTRY                                                               |
| price_type         | STANDARD                                                              |
| amount             | parsed price_text                                                     |
| currency_code      | EUR                                                                   |
| effective_from     | 2026-05-08                                                            |
| effective_to       | null                                                                  |
| status             | ACTIVE                                                                |
| promotion_id       | null                                                                  |
| reason             | Initial country standard price imported from FitnessBoutique scraping |
| created_by_user_id | 1                                                                     |
| source_price_text  | price_text                                                            |

## Database compatibility notes

The generated prices respect the current `pct_core.price` constraints:

* `price_scope = COUNTRY`
* `country_code = FR`, resolved later to an existing country row
* `store_id = null`
* `price_type = STANDARD`
* `promotion_id = null`
* `effective_to = null`

The existing reference data used later during insertion is:

```text
country: FR
user_account: id 1, admin@pct.local
```

````

