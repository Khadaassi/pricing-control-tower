# Data Generation — Sales Dataset (MVP)

## 1. Objectif

Générer un dataset de ventes simulées cohérent avec le modèle métier du projet Pricing Control Tower.

Ce dataset est utilisé pour :

- alimenter la table `pct_core.sales_transaction`
- permettre les analyses via dbt
- simuler des cas réalistes pour les KPI
- préparer les futures analyses d'anomalies

---

## 2. Hypothèses générales

- Une ligne = une ligne de ticket de caisse
- La quantité peut être supérieure à 1
- Le prix payé est toujours issu de la table `price`
- La priorité est donnée au prix magasin sur le prix pays
- Une promotion active est appliquée si un prix promo est disponible
- Les données sont déterministes et reproductibles (seed fixée)

---

## 3. Génération des ventes

Chaque vente est générée selon les étapes suivantes :

1. Sélection aléatoire d'un produit actif
2. Sélection aléatoire d'un magasin
3. Génération d'une date de transaction
4. Sélection du prix actif à la date
5. Calcul de la quantité
6. Calcul du revenu (`quantity × unit_price`)
7. Export dans un fichier CSV

---

## 4. Distribution des quantités (T48)

### Objectif

Éviter une distribution uniforme artificielle et introduire une variabilité simple et explicable.

### Logique retenue

La quantité est calculée à partir de 3 facteurs principaux.

### 4.1 Variabilité produit

Chaque produit est associé implicitement à un niveau de volume :

- faible volume
- volume moyen
- volume élevé

Implémentation :

```python
product_factor = product_id % 3
```

### 4.2 Variabilité magasin

Les magasins sont répartis en deux catégories :

- magasins à faible volume
- magasins à fort volume

Implémentation :

```python
store_factor = 1 if store_id % 2 == 0 else 0
```

### 4.3 Effet promotion

Les promotions augmentent la quantité achetée :

```python
promo_boost = 1 if price_type == "PROMO" else 0
```

### 4.4 Calcul de la quantité

```python
quantity = 1 + product_factor + store_factor + promo_boost
quantity += random.choice([0, 1])
```

### Résultat attendu

| Critère | Valeur |
|---|---|
| Quantité minimale | 1 |
| Quantité maximale (avant saisonnalité) | 6 |
| Distribution | Non uniforme |
| Variabilité | Explicable |
| Comportement | Reproductible |

---

## 5. Saisonnalité simple (T49)

### Objectif

Introduire une variation temporelle simple pour rendre les analyses plus crédibles.

### Logique retenue

La saisonnalité repose sur 3 éléments :

### 5.1 Effet samedi

Le samedi est un jour à forte activité commerciale :

```python
saturday_boost = 1 if tx_date.weekday() == 5 else 0
```

### 5.2 Effet dimanche (magasins fermés)

Le dimanche est considéré comme un jour de fermeture (sauf exceptions) :

```python
if tx_date.weekday() == 6:
    if random.random() < 0.9:
        continue
```

> 90% des ventes sont ignorées — quelques ventes subsistent (cas exceptionnels).

### 5.3 Effet mensuel léger

Une variation simple est introduite sur la période :

```python
month_boost_map = {
    1: 0,
    2: 0,
    3: 1,
    4: 1,
    5: 1,
    6: 2,
}
```

Application partielle :

```python
if random.random() < 0.3:
    quantity += month_boost
```

### 5.4 Application finale

```python
quantity += saturday_boost

if random.random() < 0.3:
    quantity += month_boost

quantity = min(quantity, 8)
```

### Résultat attendu

- Plus de ventes le samedi
- Très peu de ventes le dimanche
- Légère augmentation des volumes sur certains mois
- Variation temporelle observable
- Dataset toujours stable et contrôlé

---

## 6. Contrôles de cohérence

Les contrôles suivants sont appliqués :

- `revenue = quantity × unit_price`
- cohérence `promotion_id` ↔ `price_type`
- respect des contraintes métier
- distribution des quantités vérifiée
- distribution des ventes par jour vérifiée

---

## 7. Limites du MVP

Les simplifications suivantes sont volontaires :

- pas de comportement client
- pas de corrélation produit × magasin
- pas de gestion du stock
- pas de calendrier de jours fériés
- pas de saisonnalité avancée (ex : météo, événements)
- pas de modélisation statistique complexe

---

## 8. Conclusion

Le dataset généré :

- est cohérent avec le modèle métier
- présente une variabilité réaliste
- reste simple, explicable et reproductible
- est directement exploitable pour :
  - ingestion en base
  - dbt
  - API
  - KPI
  - détection d'anomalies
