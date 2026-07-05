# Pricing Workflow Knowledge

This document contains business-oriented knowledge about the price change workflow.
It is indexed in the RAG corpus so the chatbot can answer workflow questions without calling the LLM blindly.

---

## Explique le workflow de changement de prix

Le workflow de changement de prix permet de soumettre, valider ou refuser une demande de modification de prix.

Étapes :
1. Une demande est créée avec le statut PENDING.
2. Un utilisateur autorisé peut l'approuver.
3. Si elle est approuvée, le nouveau prix est appliqué et une entrée PriceHistory est créée.
4. Un utilisateur autorisé peut la refuser.
5. Si elle est refusée, la raison du refus est enregistrée.

Le chatbot peut expliquer le workflow, mais il ne peut jamais approuver, refuser ou appliquer une demande.

---

## How does the price change workflow work?

A price change request starts with the PENDING status.
An authorized user can approve it, which applies the new price and creates a PriceHistory record.
An authorized user can reject it, which stores the rejection reason.

The chatbot can explain the workflow, but it cannot approve, reject, or apply a price change.

---

## Pourquoi une demande reste pending ?

Une demande reste PENDING lorsqu'elle n'a pas encore été approuvée ou rejetée par un utilisateur autorisé.

Causes possibles :
- L'utilisateur habilité n'a pas encore traité la demande.
- La justification doit encore être vérifiée.
- L'impact marge ou prix doit être analysé.
- La demande est en attente de validation dans le workflow.

Prochaine étape recommandée :
Consulter la demande et vérifier qui peut l'approuver ou la refuser selon les permissions RBAC.

---

## Why does a request stay pending?

A request stays PENDING when it has not yet been approved or rejected by an authorized user.

Possible reasons:
- The authorized user has not yet processed the request.
- The justification still needs to be verified.
- The margin or price impact still needs to be analyzed.
- The request is waiting for validation in the workflow.

Recommended next step:
Check the request and verify who can approve or reject it based on RBAC permissions.

---

## Statuts du workflow

- **PENDING** : demande créée, en attente de décision.
- **APPROVED** : demande approuvée, nouveau prix appliqué.
- **REJECTED** : demande refusée, raison enregistrée.

Le chatbot peut lister les demandes par statut (pending, approved, rejected) mais ne peut pas modifier leur statut.
