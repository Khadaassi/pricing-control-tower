# Scraping Source Analysis — FitnessBoutique

## Objective

This document validates the external product catalog source selected for Sprint 6 of the Pricing Control Tower project.

The goal is to confirm that the selected website exposes enough product data through static HTML to support the ingestion pipeline:

Scraping → JSON export → Business transformation → PostgreSQL insertion → Validation

## Selected source

Website: FitnessBoutique France  
Base URL: https://www.fitnessboutique.fr

Selected MVP collection:

https://www.fitnessboutique.fr/collections/musculation-accessoire

## Scope

The MVP focuses on sport equipment and accessories only.

Included:
- bodybuilding accessories
- belts
- straps
- weighted vests
- small fitness equipment

Excluded:
- nutrition products
- food supplements
- personal data
- checkout or customer account data

## HTML validation

The page was inspected with Scrapy Shell.

Command:

```bash
uv run scrapy shell "https://www.fitnessboutique.fr/collections/musculation-accessoire"
````

## Product container

Products are available in the HTML through the following selector:

```python
response.css("product-card")
```

This selector is preferred over generic list items because the page also contains promotional blocks.

## Target fields

| Raw field           | CSS selector                                             | Required | Notes                                      |
| ------------------- | -------------------------------------------------------- | -------: | ------------------------------------------ |
| external_product_id | `input.js-compare-checkbox::attr(data-product-id)`       |      Yes | External Shopify product ID                |
| product_url         | `input.js-compare-checkbox::attr(data-product-url)`      |      Yes | Relative product URL                       |
| brand               | `.card__vendor::text`                                    |      Yes | Product brand                              |
| name                | `.card__title a::text`                                   |      Yes | Product name                               |
| description         | `.card__subtitle::text`                                  |       No | Some products may not have a subtitle      |
| price_text          | `.price__current::text`                                  |      Yes | Raw French price format                    |
| original_price_text | `.price__was::text`                                      |       No | Present only for discounted products       |
| availability_text   | `.product-inventory__status::text`                       |       No | Example: En stock                          |
| inventory_level     | `.product-inventory__status::attr(data-inventory-level)` |       No | Example: normal, backordered               |
| image_url           | `img.card__main-image::attr(data-src)`                   |      Yes | Must be normalized from `//` to `https://` |
| image_alt           | `img.card__main-image::attr(alt)`                        |       No | Useful for traceability                    |

## Data quality notes

* Product URLs may appear multiple times globally, so extraction must be done per `product-card`.
* Image URLs are stored in `data-src`, not always in `src`.
* `src` may contain a placeholder SVG and should not be used as the main source.
* Prices are extracted as raw text and will be cleaned during the transformation step.
* Category is derived from the collection URL, not from each product card.

## Business mapping preview

| Raw field     | Future pct_core target                         |
| ------------- | ---------------------------------------------- |
| category_code | product_family.code                            |
| category_name | product_family.name                            |
| brand         | product.brand                                  |
| name          | product.name                                   |
| description   | product.description                            |
| image_url     | product_image.image_url                        |
| price_text    | price.amount after transformation              |
| product_url   | source traceability field, if stored or logged |

## Decision

FitnessBoutique is validated as the Sprint 6 MVP scraping source.

The website is exploitable with Scrapy only and exposes the required product catalog fields in static HTML.
