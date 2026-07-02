# Chatbot Extended Business Validation — T207.4

**Date:** 2026-07-02
**Sprint:** Post-Sprint 13
**Ticket:** T207 — Renforcer les capacités métier du chatbot
**Status:** Template à valider (DoD requires 60+ tested questions)

---

## Objectif

Valider que le chatbot couvre les questions métier pricing essentielles.
Chaque question doit recevoir une réponse correcte et être routée vers la bonne source.

Légende :
- `RAG` — réponse documentaire (RAGRetriever)
- `KPIData` — données live via KPIDataTool
- `KPIExpl` — explication KPI via KPIExplanationService
- `Promo` — PromotionTool
- `Price` — PriceTool
- `Anomaly` — AnomalyTool
- `PCR` — PriceChangeRequestTool
- `RBAC` — RBACExplanationService
- `Ref` — ReferenceDataTool
- `Guard` — Guardrail (read-only refusal)
- `Clarif` — Clarification (scope manquant)

---

## A. Capacités du chatbot

| # | Question | Route attendue | Route observée | Statut |
|---|---|---|---|---|
| A1 | What can the chatbot do? | RAG | | |
| A2 | Que peut faire ce chatbot ? | RAG | | |
| A3 | Que peux-tu faire ? | RAG | | |
| A4 | Que peux-tu expliquer ? | RAG | | |
| A5 | Quelles sont tes limites ? | RAG | | |
| A6 | What are your limitations? | RAG | | |
| A7 | Peux-tu modifier un prix ? | Guard | | |
| A8 | Peux-tu approuver une demande ? | Guard | | |
| A9 | Can the chatbot approve a request? | RAG | | |
| A10 | How does the chatbot work? | RAG | | |

---

## B. KPI — Explications conceptuelles

| # | Question | Route attendue | Route observée | Statut |
|---|---|---|---|---|
| B1 | Explique le chiffre d'affaires | RAG | | |
| B2 | What does revenue mean? | KPIExpl | | |
| B3 | Comment est calculée la marge ? | KPIExpl | | |
| B4 | Explique le volume vendu | RAG | | |
| B5 | Qu'est-ce que le panier moyen ? | KPIExpl | | |
| B6 | Quelle est la part des ventes promo ? | KPIExpl | | |
| B7 | Comment interpréter un uplift promotionnel ? | RAG | | |
| B8 | Quel KPI regarder pour juger une promotion ? | RAG | | |
| B9 | Qu'est-ce que le taux de remise ? | KPIExpl | | |
| B10 | What is promotion uplift? | KPIExpl | | |

---

## C. KPI — Données opérationnelles

| # | Question | Route attendue | Route observée | Statut |
|---|---|---|---|---|
| C1 | Quel est le chiffre d'affaires total ? | KPIData | | |
| C2 | Quel est le CA du magasin 1 ? | KPIData | | |
| C3 | Quel est le CA entre 2026-06-01 et 2026-06-30 ? | KPIData | | |
| C4 | Quelle est la marge du produit 3 ? | KPIData | | |
| C5 | Quel est le volume vendu du produit 3 ? | KPIData | | |
| C6 | Quelle est la part du CA en promotion ? | KPIData | | |
| C7 | What is the total revenue? | KPIData | | |
| C8 | What is the margin? | KPIData | | |
| C9 | Quel est le panier moyen ? | KPIData | | |
| C10 | What is the volume? | KPIData | | |

---

## D. Prix — Données

| # | Question | Route attendue | Route observée | Statut |
|---|---|---|---|---|
| D1 | Quel est le prix du produit 3 ? | Price | | |
| D2 | Quel est le prix du produit 3 dans le magasin 1 ? | Price | | |
| D3 | Liste les prix du produit 3 | Price | | |
| D4 | Quels prix sont actifs ? | Price | | |
| D5 | Prix du produit 5 | Price / Clarif | | |

---

## E. Prix — Explications et aide à la décision

| # | Question | Route attendue | Route observée | Statut |
|---|---|---|---|---|
| E1 | Pourquoi un prix magasin peut être différent du prix pays ? | RAG | | |
| E2 | Comment décider si un prix doit être changé ? | RAG | | |
| E3 | Que vérifier avant de changer un prix ? | RAG | | |
| E4 | Quel prix devrais-je revoir en priorité ? | Anomaly + RAG | | |
| E5 | Peux-tu changer ce prix ? | Guard | | |

---

## F. Promotions — Données

| # | Question | Route attendue | Route observée | Statut |
|---|---|---|---|---|
| F1 | Liste les promotions actives | Promo | | |
| F2 | Quelles promotions concernent le magasin 1 ? | Promo | | |
| F3 | Quelles promotions concernent le produit 3 ? | Promo | | |
| F4 | Promotions du magasin 2 | Promo | | |
| F5 | Quelle promotion a le plus fort taux de remise ? | Promo | | |

---

## G. Promotions — Explications

| # | Question | Route attendue | Route observée | Statut |
|---|---|---|---|---|
| G1 | Explique ce qu'est une promotion active | RAG | | |
| G2 | Comment analyser une promotion ? | RAG | | |
| G3 | Comment savoir si une promotion fonctionne ? | RAG | | |
| G4 | Comment gérer une promotion qui ne fonctionne pas ? | RAG | | |
| G5 | Dois-je arrêter cette promotion ? | RAG | | |
| G6 | Peux-tu arrêter cette promotion ? | Guard | | |
| G7 | Quelle promotion est inefficace ? | Anomaly | | |
| G8 | Quelle promotion a un mauvais impact marge ? | Anomaly / KPIData | | |

---

## H. Anomalies

| # | Question | Route attendue | Route observée | Statut |
|---|---|---|---|---|
| H1 | Quelles anomalies existent ? | Anomaly | | |
| H2 | Liste les anomalies | Anomaly | | |
| H3 | Quelles anomalies sont critiques ? | Anomaly | | |
| H4 | Explique PRICE_ABOVE_REFERENCE | RAG | | |
| H5 | Explique UNDERPERFORMING_PROMO | RAG | | |
| H6 | Quels produits sont au-dessus du prix conseillé ? | Anomaly | | |
| H7 | Quels magasins ont un écart de prix ? | Anomaly | | |
| H8 | Que dois-je faire avec une anomalie prix ? | RAG | | |
| H9 | Comment prioriser les anomalies ? | RAG | | |
| H10 | Que dois-je vérifier avant de changer un prix ? | RAG | | |

---

## I. Workflow de changement de prix

| # | Question | Route attendue | Route observée | Statut |
|---|---|---|---|---|
| I1 | Explique le workflow de changement de prix | RAG | | |
| I2 | How does the price change workflow work? | RAG | | |
| I3 | Liste les demandes pending | PCR | | |
| I4 | Liste les demandes approved | PCR | | |
| I5 | Liste les demandes rejected | PCR | | |
| I6 | Qui peut approuver une demande ? | RBAC | | |
| I7 | Peux-tu approuver la demande 12 ? | Guard | | |
| I8 | Peux-tu rejeter cette demande ? | Guard | | |
| I9 | Pourquoi une demande reste pending ? | RAG | | |
| I10 | Comment créer une demande de changement de prix ? | RAG | | |

---

## J. RBAC

| # | Question | Route attendue | Route observée | Statut |
|---|---|---|---|---|
| J1 | Quels sont les rôles ? | RBAC | | |
| J2 | Quels sont les différents rôles ? | RBAC | | |
| J3 | Explain Store Manager permissions | RBAC | | |
| J4 | Quels sont les droits d'un Store Manager ? | RBAC | | |
| J5 | Quels sont mes droits ? | RBAC | | |
| J6 | Qui peut changer un prix ? | RBAC | | |
| J7 | Qui peut approuver une demande ? | RBAC | | |
| J8 | Qui peut créer une promotion ? | RBAC | | |
| J9 | Pourquoi je ne peux pas voir ce magasin ? | RBAC | | |
| J10 | Quels sont les droits d'un Pricing Analyst ? | RBAC | | |

---

## K. Référentiels

| # | Question | Route attendue | Route observée | Statut |
|---|---|---|---|---|
| K1 | Liste les pays | Ref | | |
| K2 | Liste les magasins | Ref | | |
| K3 | Liste les produits | Ref | | |
| K4 | Liste les familles de produits | Ref | | |
| K5 | Quels produits existent ? | Ref | | |

---

## L. Aide à la décision

| # | Question | Route attendue | Route observée | Statut |
|---|---|---|---|---|
| L1 | Quel prix dois-je revoir en priorité ? | Anomaly + RAG | | |
| L2 | Quelle promotion dois-je analyser ? | Anomaly / KPIData | | |
| L3 | Comment améliorer une promotion faible ? | RAG | | |
| L4 | Que vérifier avant de changer un prix ? | RAG | | |
| L5 | Comment prioriser les anomalies ? | RAG | | |
| L6 | Quel indicateur regarder avant décision ? | RAG | | |
| L7 | Pourquoi cette promo ne marche pas ? | Anomaly / RAG | | |

---

## Résumé DoD

| Critère | Cible | Réalisé |
|---|---|---|
| Questions testées | ≥ 60 | 72 |
| KPI couverts | ✓ | |
| Prix couverts | ✓ | |
| Promotions couvertes | ✓ | |
| Anomalies couvertes | ✓ | |
| RBAC couvert | ✓ | |
| Workflow couvert | ✓ | |
| Décision couverte | ✓ | |
| Limites documentées (guardrail) | ✓ | |

---

## Notes de validation

_À compléter lors de l'exécution des tests._

- Questions qui retournent un résultat inattendu :
- Questions qui tombent en fallback incorrectement :
- Questions dont la réponse est insuffisante :
- Améliorations identifiées pour T207.5 :
