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

## Comment savoir si une promotion fonctionne ?

Une promotion fonctionne si elle améliore la performance commerciale sans dégrader excessivement la marge.

Pour l’évaluer, il faut vérifier :
- le chiffre d’affaires généré pendant la promotion ;
- le volume vendu ;
- l’uplift par rapport à une période de référence ;
- l’impact sur la marge ;
- la part du CA en promotion ;
- le taux de remise ;
- les anomalies associées comme UNDERPERFORMING_PROMO ou INEFFECTIVE_DISCOUNT.

Une promotion ne doit pas être jugée uniquement sur le chiffre d’affaires. Une hausse du CA peut masquer une baisse de marge.

Prochaine étape recommandée :
Comparer les KPI avant et pendant la promotion, puis vérifier les anomalies liées à cette promotion.

## Différence entre promotion active et promotion en cours

Le statut `ACTIVE` est un statut technique : il signifie que la promotion n'a pas été manuellement désactivée. Il est distinct du statut de période :

| Statut de période | Signification |
|---|---|
| En cours | Aujourd'hui est compris entre la date de début et la date de fin |
| À venir | La date de début est dans le futur |
| Expiré | La date de fin est dépassée |

Une promotion avec statut `ACTIVE` peut avoir une période expirée si elle n'a pas été clôturée manuellement dans l'application. Pour vérifier si une promotion est réellement en cours aujourd'hui, contrôlez à la fois le statut technique et la période affichée.

## Quand arrêter ou ne pas prolonger une promotion ?

Avant de décider d'arrêter ou de ne pas prolonger une promotion, analysez les indicateurs suivants :

1. **Uplift de revenu** — le CA pendant la promotion est-il supérieur au CA de la période de référence ?
2. **Volume vendu** — les ventes ont-elles augmenté ?
3. **Impact sur la marge** — la remise a-t-elle dégradé la marge sous le seuil acceptable ?
4. **Anomalies** — une anomalie UNDERPERFORMING_PROMO ou INEFFECTIVE_DISCOUNT a-t-elle été détectée ?
5. **Durée** — la promotion est-elle trop récente pour être correctement évaluée ?

Recommandations :
- Uplift négatif ET marge dégradée → envisager l'arrêt
- Uplift faible mais marge stable → analyser plus longtemps ou ajuster la remise
- Uplift fort mais marge dégradée → revoir le taux de remise
- Ne jamais arrêter une promotion sans analyser les KPI et les anomalies associées

Le chatbot peut identifier les anomalies et expliquer les KPI associés. La décision d'arrêt ou de non-prolongation doit être prise par un utilisateur autorisé dans l'application.