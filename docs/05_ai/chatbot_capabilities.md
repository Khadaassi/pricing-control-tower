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

## What the chatbot cannot do

The chatbot is strictly read-only. It never modifies data.

- Cannot apply a price change
- Cannot approve or reject a price change request
- Cannot create, modify, or deactivate a promotion
- Cannot update any record in the system
- Cannot bypass RBAC — the same access rules apply to the chatbot as to the application
- Cannot decide for the user (it advises, the user decides)

If you ask the chatbot to perform an action, it will explain that it is read-only and guide you toward the correct manual workflow.

## Supported languages

The chatbot understands and responds in French and English. You can switch languages at any time.

## How the chatbot works

The chatbot uses two complementary approaches:

**Tool Calling** — for operational data (live figures from the backend): promotions, prices, anomalies, KPI numbers, price change requests, reference data.

**RAG (Retrieval-Augmented Generation)** — for conceptual questions (business rules, workflow explanations, KPI definitions, RBAC, decision support): the chatbot retrieves relevant documentation and generates a natural language answer.
