# Promotion Knowledge for Pricing Users

## What is a promotion

A promotion is a temporary price reduction applied to one or more products, at the country level or store level, for a defined period. Promotions are created by authorized roles (Country Director, Pricing Analyst) and follow the same scope rules as regular prices.

## Promotion scope

Promotions can be scoped at two levels:

**Country-level promotion** — applies to all stores in a country. All stores selling the product receive the promotional price during the promotion period.

**Store-level promotion** — applies to a specific store only. Other stores are unaffected.

A country-level and store-level promotion cannot overlap for the same product and period (business rule: no overlapping promotions for the same scope).

## Promotion types

| Type | Description |
|---|---|
| PERCENTAGE | Discount expressed as a percentage of the reference price (e.g., −15%) |
| FIXED_PRICE | A fixed selling price set for the promotion period (e.g., €9.99) |

## Active promotion

A promotion is active when today's date falls within its start and end date range and it has not been manually deactivated.

To list active promotions, ask:
- "Liste les promotions actives"
- "Quelles promotions sont actives pour le magasin 1 ?"
- "Quelles promotions concernent le produit 3 ?"

## Analysing a promotion

To assess whether a promotion is working, check:

1. **Revenue uplift** — did total revenue increase during the promotion compared to the baseline period?
2. **Volume uplift** — did the number of units sold increase?
3. **Margin impact** — did margin deteriorate below an acceptable threshold?
4. **Promotion sales share** — what proportion of sales happened under the promotion?
5. **Discount rate** — how deep is the discount relative to the reference price?

A promotion is considered successful if it generates positive revenue and volume uplift without eroding margin below the business floor.

## Underperforming promotion

An UNDERPERFORMING_PROMO anomaly is raised when a promotion generates revenue more than 10% below the expected baseline.

Possible causes:
- Promotion is too recent to show uplift (insufficient data)
- Discount depth is too low to attract demand
- Product is not well-known or not in season
- Promotion is cannibalizing another product

Decision support: Before stopping an underperforming promotion, check how long it has been running, what the baseline volume was, and whether other promotions are running simultaneously on competing products.

## Ineffective discount

An INEFFECTIVE_DISCOUNT anomaly is raised when a discount of 20% or more does not produce a measurable volume uplift.

This usually means the price reduction is not changing customer behaviour — the product may already be selling at a high rate, or customers are insensitive to the discount at this product level.

Decision support: Consider changing the discount mechanic (bundle offer, loyalty offer) or reducing the discount depth if margin erosion is significant.

## How to handle a promotion that is not working

The chatbot cannot stop or modify a promotion. The correct workflow is:

1. Identify the underperforming promotion using anomaly data or KPI analysis
2. Analyse the root cause (volume, revenue, margin, discount depth)
3. Decide whether to deactivate, modify, or extend the promotion
4. Use the application interface to deactivate the promotion (requires appropriate role)

The chatbot can help with steps 1 and 2 by listing anomalies and explaining KPI results. Steps 3 and 4 must be done by the user in the application.

## Who can create and manage promotions

| Action | Required role |
|---|---|
| Create a country-level promotion | Country Director, Pricing Analyst |
| Create a store-level promotion | Store Manager, Country Director |
| Deactivate a promotion | Country Director, Pricing Analyst |

The chatbot cannot create, modify, or deactivate promotions.
