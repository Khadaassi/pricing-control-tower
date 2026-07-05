# Chatbot Capabilities and Limitations

## What the chatbot can do

The Pricing Control Tower chatbot is a read-only assistant. It helps pricing users understand data, concepts, and decisions — it never modifies anything.

### Explain KPIs

The chatbot explains every pricing KPI: revenue, margin, volume, average selling price, promotion sales share, promotional uplift, and discount rate.

Ask:
- "What is revenue?"
- "How is margin calculated?"
- "Qu'est-ce que le panier moyen ?"
- "Comment interpréter un uplift promotionnel ?"

### Answer questions about operational data

The chatbot retrieves live data from the backend:

- Active promotions (by store, by product, by country)
- Prices (by product, by store)
- Pricing anomalies (UNDERPERFORMING_PROMO, INEFFECTIVE_DISCOUNT, PRICE_ABOVE_REFERENCE, INTER_STORE_PRICE_GAP)
- Price change requests (pending, approved, rejected)
- KPI summary (revenue, margin, volume, promo share)
- Reference data (countries, stores, products, product families)

Ask:
- "Liste les promotions actives"
- "Quelles anomalies existent pour mon magasin ?"
- "Quel est le chiffre d'affaires du magasin 1 ?"
- "Liste les demandes de changement de prix en attente"

### Explain business concepts

The chatbot explains:

- Pricing workflow: how a price change request is created, reviewed, approved, and applied
- Business rules: price scope, promotion scope, audit trail
- Anomaly types and their business meaning
- RBAC roles and permissions

Ask:
- "Comment fonctionne le workflow de changement de prix ?"
- "Que signifie PRICE_ABOVE_REFERENCE ?"
- "Quels sont les rôles et leurs droits ?"

### Support pricing decisions (advisory only)

The chatbot can suggest analysis steps, highlight anomalies to investigate, and recommend what to check before acting. It never decides for the user.

Ask:
- "Quelles anomalies dois-je regarder en priorité ?"
- "Que vérifier avant de changer un prix ?"
- "Comment analyser une promotion qui ne fonctionne pas ?"

## What the chatbot can explain

The chatbot can explain the following topics:

- **KPIs**: revenue (chiffre d'affaires), margin (marge), volume, average order value (panier moyen), promotional uplift, discount rate, price gap, promotion sales share (part du CA en promotion)
- **Anomalies**: PRICE_ABOVE_REFERENCE, UNDERPERFORMING_PROMO, INEFFECTIVE_DISCOUNT, INTER_STORE_PRICE_GAP — what they mean and what to check
- **Business rules**: pricing workflow rules, price scope, promotion scope, audit trail
- **Pricing workflow**: how a price change request is created, submitted, reviewed, approved, and applied
- **RBAC roles and permissions**: who can do what, what each role can see, why access differs between users
- **Its own capabilities and limits**: what the chatbot can and cannot do

Ask:
- "Que peux-tu expliquer ?"
- "Qu'est-ce que tu peux expliquer ?"
- "Quels sujets peux-tu couvrir ?"
- "What can you explain?"

## What the chatbot cannot do — Limites du chatbot

The chatbot is strictly read-only. It never modifies data.

| Limit | Detail |
|---|---|
| Cannot apply a price change | Pricing actions must go through the manual workflow |
| Cannot approve or reject a price change request | Approval is a human decision in the application |
| Cannot create, modify, or deactivate a promotion | Promotion management is outside the chatbot scope |
| Cannot write to the database | The chatbot is read-only: no inserts, no updates, no deletes |
| Cannot bypass RBAC | The same access rules apply to the chatbot as to the rest of the application |
| Cannot decide for the user | The chatbot advises; the user decides |
| Needs context for data | For live data (KPIs, prices, anomalies), the chatbot needs at minimum a product, store, or period |

If you ask the chatbot to perform an action, it will explain that it is read-only and guide you toward the correct manual workflow.

Ask:
- "Quelles sont tes limites ?"
- "Que ne peux-tu pas faire ?"
- "What are your limitations?"
- "Can you approve a price change?"

## Supported languages

The chatbot understands and responds in French and English. You can switch languages at any time.

## How the chatbot works

The chatbot uses two complementary approaches:

**Tool Calling** — for operational data (live figures from the backend): promotions, prices, anomalies, KPI numbers, price change requests, reference data.

**RAG (Retrieval-Augmented Generation)** — for conceptual questions (business rules, workflow explanations, KPI definitions, RBAC, decision support): the chatbot retrieves relevant documentation and generates a natural language answer.
