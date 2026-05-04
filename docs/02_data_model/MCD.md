# MCD simplifié — Pricing Control Tower

## 1. Objectif

Ce modèle conceptuel de données (MCD) décrit les principales entités métier du système Pricing Control Tower ainsi que leurs relations.

Il constitue la base de référence pour :

* la conception de la base de données PostgreSQL
* l’implémentation des modèles SQLAlchemy
* la mise en place des migrations Alembic
* la compréhension globale du système lors de la soutenance

---

## 2. Entités principales

### Référentiel

* **Country** : pays dans lequel opèrent les magasins
* **Store** : point de vente physique ou logique
* **Product** : produit vendu
* **ProductFamily** : regroupement de produits
* **ProductImage** : illustration associée à un produit

---

### Pricing

* **Price** : prix d’un produit dans un magasin donné
* **PriceHistory** : historique des modifications de prix

---

### Promotions

* **Promotion** : promotional action applied to a single **Product**, scoped to a country or a specific store

---

### Performance

* **Sale** : vente réalisée (fait métier principal pour l’analyse)

---

### Workflow & traçabilité

* **PriceChangeRequest** : demande de modification de prix
* **User** : utilisateur du système (création / validation)
* **AuditLog** : journal des actions utilisateurs

---

## 3. Relations principales

### Référentiel

* Un **Country** possède plusieurs **Store**

* Un **Store** appartient à un seul **Country**

* Un **Product** appartient à une **ProductFamily**

* Un **Product** peut avoir plusieurs **ProductImage**

---

### Pricing

* Un **Product** est associé à plusieurs **Price**

* Un **Price** est défini pour un **Product** et un **Store**

* Un **Price** possède plusieurs entrées dans **PriceHistory**

---

### Promotions

* A **Promotion** targets exactly one **Product**
* A **Promotion** is scoped to a **Country** (optionally a specific **Store**)
* A **Promotion** can be linked to a **Price**
* A **Promotion** can be associated with **Sale** transactions

---

### Performance

* Une **Sale** concerne un **Product**
* Une **Sale** est réalisée dans un **Store**
* Une **Sale** peut être associée à une **Promotion**

---

### Workflow

* Un **PriceChangeRequest** concerne un **Product**

* Un **PriceChangeRequest** concerne un **Store**

* Un **PriceChangeRequest** est lié à un **Price**

* Un **User** crée ou valide un **PriceChangeRequest**

---

### Traçabilité

* Un **User** génère des entrées dans **AuditLog**

---

## 4. Règles métier principales

* Un prix est toujours défini pour un couple **Product / Store**
* Un prix peut être de type **STANDARD** ou **PROMO**
* Un prix peut être marqué comme **recommandé par le pays** (booléen)
* Toute modification de prix doit être tracée dans **PriceHistory**
* Toute action utilisateur importante doit être tracée dans **AuditLog**

---

## 5. Simplifications retenues pour le MVP

Afin de maintenir un niveau de complexité maîtrisé pour la première version :

* Le **canal (online / magasin)** n’est pas modélisé explicitement
* Le ciblage des promotions est simplifié (pas d’entité `PromotionTarget`)
* La recommandation pays est portée par un attribut de l’entité **Price**
* Le workflow de changement de prix est directement relié à **Price**

Ces choix permettent une implémentation progressive tout en restant évolutifs.

---

## 6. Évolutions prévues

Le modèle pourra évoluer dans les versions suivantes pour intégrer :

* Une entité **Channel** (online / instore)
* Une entité **PromotionTarget** pour un ciblage plus fin
* Des règles de pricing plus avancées
* Des optimisations pour la couche analytique (`pct_analytics`)

---

## 7. Conclusion

Ce MCD fournit une base cohérente, compréhensible et exploitable pour :

* la création du modèle logique (MLD)
* l’implémentation en base de données
* le développement backend

Il reflète un compromis entre simplicité (MVP) et évolutivité.
