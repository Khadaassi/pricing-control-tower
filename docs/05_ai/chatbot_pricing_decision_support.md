# Pricing Decision Support

The chatbot advises — it never decides. Use these guidelines to interpret data and decide when to act.

## When to investigate a price

Investigate a price when:
- A PRICE_ABOVE_REFERENCE anomaly is raised for a product in your store
- A significant price gap appears between your store and the country average (INTER_STORE_PRICE_GAP)
- Revenue is declining but volume is stable (possible price point issue)
- Margin has dropped below the business floor

Do not act immediately. First verify that the anomaly is not a data issue and that the price gap has no legitimate business justification.

## What to check before changing a price

Before creating a price change request, check in order:

1. **Current price and reference price** — is the gap significant?
2. **Margin at current price** — is margin acceptable? What will margin be at the new price?
3. **Volume trend** — is the current price affecting demand?
4. **Promotion history** — is there an active or recent promotion that explains the anomaly?
5. **Competitive context** — is the price gap versus country reference intentional (local costs, premium positioning)?
6. **RBAC scope** — do you have the right to request a price change for this product and store?

Only create a price change request when you have confirmed the price needs to change and you have a clear business justification.

## When to create a price change request

Create a price change request when:
- You have confirmed a price is incorrect or non-competitive
- You have analysed the margin impact and it is acceptable
- No active promotion already covers this product
- You have the necessary role and scope to create a request

The request will enter the validation workflow and require approval before being applied.

## When not to act

Do not create a price change request when:
- The anomaly is explained by an active promotion
- The price gap is intentional (premium positioning, cost difference)
- You have not yet verified the margin impact
- Another price change request is already pending for the same product and store
- The anomaly is flagged as low priority and no business impact is confirmed

## How to interpret a price gap between store and country

A store price higher than the country reference (PRICE_ABOVE_REFERENCE) is not automatically an error. Check:
- Is there a specific cost justification for this store?
- Has the price been deliberately set at store level?
- Is there a pending price change request to align it?

A large gap across multiple stores (INTER_STORE_PRICE_GAP) may indicate a systematic issue — compare all stores for this product before acting.

## How to analyse a promotion that is not working

When an UNDERPERFORMING_PROMO anomaly is raised:

1. Check the promotion period — was it too short to measure uplift?
2. Check the discount depth — is the discount large enough to change behaviour?
3. Check volume during the promotion — did units sold increase?
4. Check margin — did margin deteriorate despite low uplift?
5. Check whether a competing promotion is running simultaneously

If volume did not increase and margin deteriorated: the promotion is not generating incremental demand and is only reducing revenue. Investigate whether to deactivate it.

If volume increased but revenue decreased: the discount may be too deep. Analyse whether reduced margin at higher volume is still profitable.

## How to prioritise anomalies

Not all anomalies require immediate action. Use this priority order:

| Priority | Anomaly | Reason |
|---|---|---|
| 1 | PRICE_ABOVE_REFERENCE with large gap | Immediate customer impact |
| 2 | INEFFECTIVE_DISCOUNT with margin erosion | Financial loss with no demand benefit |
| 3 | UNDERPERFORMING_PROMO with significant revenue gap | Revenue shortfall |
| 4 | INTER_STORE_PRICE_GAP with no justification | Consistency issue |

Focus on anomalies with confirmed financial impact first. Anomalies that may have a legitimate business explanation can be reviewed later.

## Which KPI to look at before a decision

| Decision | KPI to check first |
|---|---|
| Should I change this price? | Margin at current price, Price gap, PRICE_ABOVE_REFERENCE anomaly |
| Should I extend this promotion? | Revenue uplift, Volume uplift, Margin during promo |
| Should I stop this promotion? | UNDERPERFORMING_PROMO, INEFFECTIVE_DISCOUNT, Margin |
| Which anomaly to address first? | Financial impact (revenue gap, margin loss) |
| Is this promotion creating demand? | Volume uplift, Promo sales share |

## What the chatbot recommends vs what the user decides

The chatbot suggests analysis steps and highlights data signals. It does not decide.

The chatbot will say:
- "Je vous recommande de vérifier..."
- "Il serait utile de comparer..."
- "Avant de décider, vérifiez..."

The chatbot will not say:
- "Vous devez changer ce prix"
- "Arrêtez cette promotion"
- "Approuvez cette demande"

The decision and the action are always the user's responsibility.

## Comment décider si un prix doit être changé ?

Un prix doit être revu lorsqu’un indicateur métier montre un risque ou une opportunité.

Avant de proposer un changement de prix, il faut vérifier :
- l’écart entre le prix magasin et le prix pays ;
- la marge ;
- le volume vendu ;
- le chiffre d’affaires ;
- les anomalies pricing ;
- l’historique des changements de prix ;
- les promotions actives sur le produit.

Le chatbot peut recommander une analyse ou suggérer de créer une demande de changement de prix, mais il ne peut jamais appliquer le changement automatiquement.

Prochaine étape recommandée :
Consulter les anomalies prix et comparer le prix magasin au prix de référence pays.