# Data Generation — Sales Dataset (MVP)

## Objectif

Générer un dataset de ventes simulées cohérent avec le modèle métier du projet Pricing Control Tower.

Ce dataset est utilisé pour :

- alimenter la table `pct_core.sales_transaction`
- permettre les analyses via dbt
- simuler des cas réalistes pour les KPI

---

## Hypothèses générales

- Une ligne = une ligne de ticket de caisse
- La quantité peut être supérieure à 1
- Le prix est toujours issu de la table `price`
- La priorité est donnée au prix magasin sur le prix pays
- Une promotion active est automatiquement appliquée si disponible

---

## Distribution des quantités (T48)

### Objectif

Éviter une distribution artificielle uniforme des quantités vendues.

Introduire une variabilité simple, explicable et reproductible.

---

### Logique retenue

La quantité vendue est calculée à partir de 3 facteurs :

#### 1. Variabilité produit

Chaque produit appartient implicitement à une catégorie de volume :

- produits à faible volume
- produits à volume moyen
- produits à fort volume

Implémentation :

```python
product_factor = product_id % 3
2. Variabilité magasin

Les magasins sont segmentés en deux catégories :

magasins à faible volume
magasins à fort volume

Implémentation :

store_factor = 1 if store_id % 2 == 0 else 0
3. Effet promotion

Une promotion augmente la probabilité d’achat en quantité plus élevée.

Implémentation :

promo_boost = 1 if price_type == "PROMO" else 0
4. Quantité finale
quantity = 1 + product_factor + store_factor + promo_boost
quantity += random.choice([0, 1])
Résultat
Quantité minimale : 1
Quantité maximale : 6
Distribution non uniforme
Variabilité explicable
Reproductible (seed fixée)
Limites (MVP)
Pas de corrélation produit × magasin
Pas de segmentation client
Pas de saisonnalité (gérée dans T49)

Ces simplifications sont volontaires pour rester dans un MVP maîtrisé.



---


---