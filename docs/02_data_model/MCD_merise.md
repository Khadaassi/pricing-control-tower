# MCD — Formalisme Merise — Pricing Control Tower

_Dernière vérification : 2026-08-24_

## 1. Objet

Ce document est le **Modèle Conceptuel de Données (MCD)** du schéma `pct_core`, exprimé selon le formalisme Merise (entités porteuses de leurs propres attributs uniquement, associations porteuses des cardinalités `(min,max)` — sans clé étrangère au niveau conceptuel : les clés étrangères n'apparaissent qu'au passage au MLD, section 5).

Il remplace, pour la preuve du critère « les modélisations respectent la méthode et le formalisme Merise », le diagramme `MCD.png` du dépôt, qui est en réalité un diagramme entité-relation en notation « crow's foot » (cardinalités en pattes-de-corbeau, attributs absents des entités) — utile comme vue d'ensemble rapide, mais non conforme au formalisme Merise. Ce document et `MCD.png` sont donc complémentaires : `MCD.png` pour la vue d'ensemble rapide, ce document pour la preuve formelle du formalisme Merise.

Le détail technique (types SQL, contraintes) reste dans `MLD_pct_core.md` (modèle logique) et `MPD_pct_core.md` (modèle physique PostgreSQL). Les entités et cardinalités ci-dessous sont dérivées directement de ces deux documents et du code (`backend/app/models/`, `backend/alembic/versions/`).

---

## 2. Entités et attributs

En Merise, une entité ne porte que ses **attributs propres** : les clés étrangères ne sont pas des attributs d'entité, elles sont portées par les **associations** (section 3).

| Entité | Attributs propres |
|---|---|
| **PAYS** | id (id), code, nom |
| **MAGASIN** | id (id), code, nom, ville, région, date_ouverture |
| **FAMILLE_PRODUIT** | id (id), code, nom, description |
| **PRODUIT** | id (id), code, nom, description, marque, modèle, actif |
| **IMAGE_PRODUIT** | id (id), url_image, texte_alternatif, ordre_affichage |
| **UTILISATEUR** | id (id), email, nom_complet, actif |
| **PROMOTION** | id (id), code, nom, description, type_remise, valeur_remise, date_début, date_fin, date_création, actif |
| **PRIX** | id (id), portée_prix, type_prix, montant, devise, date_effet_début, date_effet_fin, statut, motif, date_création |
| **VENTE** | id_transaction (id), date_transaction, quantité, prix_unitaire, chiffre_affaires, est_promo, portée_prix, type_prix |
| **DEMANDE_MODIF_PRIX** | id (id), montant_prix_actuel, montant_prix_demandé, statut, justification, date_effet_demandée, motif_rejet, date_rejet, date_création, date_maj |
| **HISTORIQUE_PRIX** | id_historique (id), montant_prix_précédent, montant_nouveau_prix, date_application, date_création |
| **JOURNAL_AUDIT** | id_audit (id), type_action, description, date_création |
| **ROLE** | id (id), code, nom, description |
| **PERMISSION** | id (id), code, nom, description |

---

## 3. Associations et cardinalités

Convention de lecture : pour l'association *A* entre l'entité *E1* et l'entité *E2*, la cardinalité notée côté *E1* indique, pour une occurrence de *E1*, le nombre minimum et maximum d'occurrences de *E2* auxquelles elle est liée.

| Association | Entité 1 (cardinalité) | Entité 2 (cardinalité) | Sens métier |
|---|---|---|---|
| COMPTER | PAYS (0,n) | MAGASIN (1,1) | Un pays compte 0 à n magasins ; un magasin appartient à exactement un pays |
| REGROUPER | FAMILLE_PRODUIT (0,n) | PRODUIT (1,1) | Une famille regroupe 0 à n produits ; un produit appartient à exactement une famille |
| ILLUSTRER | PRODUIT (0,n) | IMAGE_PRODUIT (1,1) | Un produit est illustré par 0 à n images ; une image illustre exactement un produit |
| RATTACHER_PAYS | PAYS (0,n) | UTILISATEUR (0,1) | Un pays est le périmètre de 0 à n utilisateurs ; un utilisateur est rattaché à 0 ou 1 pays |
| RATTACHER_MAGASIN | MAGASIN (0,n) | UTILISATEUR (0,1) | Un magasin est le périmètre de 0 à n utilisateurs ; un utilisateur est rattaché à 0 ou 1 magasin |
| CIBLER | PRODUIT (0,n) | PROMOTION (1,1) | Un produit est ciblé par 0 à n promotions ; une promotion cible exactement un produit |
| SCOPER_PAYS_PROMO | PAYS (0,n) | PROMOTION (1,1) | Un pays porte 0 à n promotions ; une promotion est scopée à exactement un pays |
| SCOPER_MAGASIN_PROMO | MAGASIN (0,n) | PROMOTION (0,1) | Un magasin porte 0 à n promotions ; une promotion est scopée à 0 ou 1 magasin |
| CREER_PROMOTION | UTILISATEUR (0,n) | PROMOTION (1,1) | Un utilisateur crée 0 à n promotions ; une promotion est créée par exactement un utilisateur |
| TARIFER | PRODUIT (0,n) | PRIX (1,1) | Un produit a 0 à n prix ; un prix concerne exactement un produit |
| SCOPER_PAYS_PRIX | PAYS (0,n) | PRIX (1,1) | Un pays porte 0 à n prix ; un prix est scopé à exactement un pays |
| SCOPER_MAGASIN_PRIX | MAGASIN (0,n) | PRIX (0,1) | Un magasin porte 0 à n prix ; un prix est scopé à 0 ou 1 magasin |
| JUSTIFIER | PROMOTION (0,n) | PRIX (0,1) | Une promotion justifie 0 à n prix ; un prix est éventuellement justifié par 0 ou 1 promotion |
| CREER_PRIX | UTILISATEUR (0,n) | PRIX (1,1) | Un utilisateur crée 0 à n prix ; un prix est créé par exactement un utilisateur |
| CONCERNER_PRODUIT_VENTE | PRODUIT (0,n) | VENTE (1,1) | Un produit apparaît dans 0 à n ventes ; une vente concerne exactement un produit |
| REALISER_VENTE | MAGASIN (0,n) | VENTE (1,1) | Un magasin réalise 0 à n ventes ; une vente est réalisée dans exactement un magasin |
| APPLIQUER_PRIX_VENTE | PRIX (0,n) | VENTE (1,1) | Un prix est appliqué à 0 à n ventes ; une vente applique exactement un prix |
| APPLIQUER_PROMO_VENTE | PROMOTION (0,n) | VENTE (0,1) | Une promotion s'applique à 0 à n ventes ; une vente applique 0 ou 1 promotion |
| CONCERNER_PRODUIT_DEMANDE | PRODUIT (0,n) | DEMANDE_MODIF_PRIX (1,1) | Un produit fait l'objet de 0 à n demandes ; une demande concerne exactement un produit |
| SCOPER_PAYS_DEMANDE | PAYS (0,n) | DEMANDE_MODIF_PRIX (1,1) | Un pays porte 0 à n demandes ; une demande est scopée à exactement un pays |
| SCOPER_MAGASIN_DEMANDE | MAGASIN (0,n) | DEMANDE_MODIF_PRIX (0,1) | Un magasin porte 0 à n demandes ; une demande est scopée à 0 ou 1 magasin |
| CONCERNER_PRIX_DEMANDE | PRIX (0,n) | DEMANDE_MODIF_PRIX (1,1) | Un prix fait l'objet de 0 à n demandes ; une demande concerne exactement un prix courant |
| DEMANDER | UTILISATEUR (0,n) | DEMANDE_MODIF_PRIX (1,1) | Un utilisateur soumet 0 à n demandes ; une demande est soumise par exactement un utilisateur |
| REJETER | UTILISATEUR (0,n) | DEMANDE_MODIF_PRIX (0,1) | Un utilisateur rejette 0 à n demandes ; une demande est rejetée par 0 ou 1 utilisateur |
| HISTORISER | DEMANDE_MODIF_PRIX (0,1) | HISTORIQUE_PRIX (1,1) | Une demande génère 0 ou 1 entrée d'historique ; une entrée d'historique historise exactement une demande |
| PRIX_PRECEDENT | PRIX (0,n) | HISTORIQUE_PRIX (1,1) | Un prix a été prix précédent dans 0 à n historiques ; un historique référence exactement un prix précédent |
| PRIX_NOUVEAU | PRIX (0,n) | HISTORIQUE_PRIX (1,1) | Un prix a été nouveau prix dans 0 à n historiques ; un historique référence exactement un nouveau prix |
| APPLIQUER_HISTORIQUE | UTILISATEUR (0,n) | HISTORIQUE_PRIX (1,1) | Un utilisateur applique 0 à n changements de prix ; un historique est appliqué par exactement un utilisateur |
| TRACER | DEMANDE_MODIF_PRIX (0,n) | JOURNAL_AUDIT (1,1) | Une demande génère 0 à n entrées d'audit ; une entrée d'audit trace exactement une demande |
| GENERER_AUDIT | UTILISATEUR (0,n) | JOURNAL_AUDIT (1,1) | Un utilisateur génère 0 à n entrées d'audit ; une entrée d'audit est générée par exactement un utilisateur |
| POSSEDER | UTILISATEUR (0,n) | ROLE (0,n) | Un utilisateur possède 0 à n rôles ; un rôle est possédé par 0 à n utilisateurs *(association porteuse : table `user_role`)* |
| ACCORDER | ROLE (0,n) | PERMISSION (0,n) | Un rôle accorde 0 à n permissions ; une permission est accordée par 0 à n rôles *(association porteuse : table `role_permission`)* |

---

## 4. Note de lecture

- Deux associations distinctes relient PRIX et HISTORIQUE_PRIX (`PRIX_PRECEDENT`, `PRIX_NOUVEAU`) car un même historique référence deux occurrences différentes de PRIX (rôle « ancien prix » et rôle « nouveau prix ») — cas classique d'association multiple entre les deux mêmes entités en Merise.
- `POSSEDER` et `ACCORDER` sont des associations plusieurs-à-plusieurs porteuses, matérialisées en base par les tables de jonction `user_role` et `role_permission` (sans attribut propre autre que les clés).
- Les cardinalités `(0,n)` côté « référentiel » (PAYS, MAGASIN, PRODUIT, UTILISATEUR) sont volontairement prudentes (minimum 0) : aucune contrainte NOT NULL en base n'impose qu'un pays ait au moins un magasin, qu'un produit ait au moins un prix, etc. au moment de la création de l'entité.

---

## 5. Correspondance avec le MLD

Chaque association ci-dessus se traduit dans `MLD_pct_core.md` par une clé étrangère portée par la table du côté `(1,1)` ou `(0,1)` :

| Association Merise | Traduction MLD |
|---|---|
| COMPTER | `store.country_id` (NOT NULL) |
| REGROUPER | `product.product_family_id` (NOT NULL) |
| ILLUSTRER | `product_image.product_id` (NOT NULL) |
| RATTACHER_PAYS / RATTACHER_MAGASIN | `user_account.country_id`, `user_account.store_id` (NULL, contrainte `ck_user_account_scope`) |
| CIBLER / SCOPER_*_PROMO / CREER_PROMOTION | `promotion.product_id`, `promotion.country_id`, `promotion.store_id`, `promotion.created_by` |
| TARIFER / SCOPER_*_PRIX / JUSTIFIER / CREER_PRIX | `price.product_id`, `price.country_id`, `price.store_id`, `price.promotion_id`, `price.created_by` |
| CONCERNER_*_VENTE / REALISER_VENTE / APPLIQUER_*_VENTE | `sales_transaction.product_id`, `.store_id`, `.price_id`, `.promotion_id` |
| *_DEMANDE / DEMANDER / REJETER | `price_change_request.product_id`, `.country_id`, `.store_id`, `.current_price_id`, `.requested_by_user_id`, `.rejected_by_user_id` |
| HISTORISER / PRIX_PRECEDENT / PRIX_NOUVEAU / APPLIQUER_HISTORIQUE | `price_history.price_change_request_id` (UNIQUE), `.previous_price_id`, `.new_price_id`, `.applied_by_user_id` |
| TRACER / GENERER_AUDIT | `audit_log.price_change_request_id`, `.performed_by_user_id` |
| POSSEDER / ACCORDER | `user_role(user_id, role_id)`, `role_permission(role_id, permission_id)` |

---

## 6. Conclusion

Ce MCD couvre les 16 entités du schéma `pct_core` en formalisme Merise strict (entités = attributs propres uniquement, associations = clés étrangères + cardinalités `(min,max)`). Il sert de preuve formelle du critère de conformité Merise et de passerelle vers le MLD et le MPD déjà documentés.
