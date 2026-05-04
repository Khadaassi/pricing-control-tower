# Cahier des Charges Fonctionnel

> **Projet :** Pricing Control Tower
> **Domaine :** Pilotage tarifaire et Intelligence Artificielle
> **Version :** 1.0 — MVP

---

## 1. Contexte du projet

Le projet Pricing Control Tower est une application web de pilotage tarifaire permettant de centraliser, analyser et piloter les prix et promotions au sein d’une organisation multi-magasins.

Ce projet est réalisé dans le cadre d’une certification professionnelle RNCP en développement IA. Il a pour objectif de démontrer la capacité à concevoir une architecture data complète, à développer une application web connectée à des services de données et à intégrer des fonctionnalités d’intelligence artificielle.

Le projet simule un contexte d’entreprise réaliste avec des contraintes de traçabilité, de gouvernance et de performance.

---

## 2. Objectifs du produit

L’application permet aux utilisateurs métiers d'intervenir sur les axes suivants :

### 2.1 Analyse et Pilotage

- **Visualisation** — Suivi des ventes en quantité et chiffre d'affaires.
- **Performance** — Analyse de l'efficacité des prix et des promotions.
- **Comparaison** — Mise en perspective des performances entre les magasins et au niveau national.

### 2.2 Pricing et Promotions

- **Consultation** — Accès aux prix standards et promotionnels (niveaux pays et magasin).
- **Historisation** — Consultation de l'historique complet des prix appliqués.
- **Efficacité promotionnelle** — Mesure de l'accélération des ventes par rapport à une *baseline*.

### 2.3 Aide à la décision et Gouvernance

- **Identification** — Détection des anomalies de performance ou des incohérences tarifaires.
- **Workflow** — Gestion d'un cycle de validation pour tout changement de prix.
- **Traçabilité** — Audit complet des actions effectuées sur la plateforme.

### 2.4 Intelligence Artificielle (Évolution)

- Explication des indicateurs clés de performance (KPI).
- Analyse des causes d'anomalies.
- Suggestions d'actions correctives (sans automatisation).

---

## 3. Périmètre du MVP

| Axe | Définition du périmètre |
|---|---|
| **Géographique** | France uniquement |
| **Organisation** | Structure multi-magasins |
| **Catalogue** | 3 familles de produits (~10 produits par famille) |
| **Pricing** | Prix nationaux et *overrides* locaux (magasin) |
| **Promotions** | Nationales et locales |
| **Données** | Flux transactionnels simulés |
| **Processus** | Workflow de création et validation manuelle des demandes |
| **Analytique** | Table centrale `obt_sales` et KPI spécifiques |

---

## 4. Utilisateurs

### Phase MVP

| Rôle | Description |
|---|---|
| **Administrateur** | Utilisateur unique disposant de l'intégralité des droits d'accès et de modification. |

### Évolutions cibles

| Rôle | Description |
|---|---|
| **Analyste** | Accès en lecture seule. |
| **Responsable Magasin** | Gestion locale. |
| **Responsable Pays** | Vision globale et stratégie. |
| **Validateur** | Pouvoir d'approbation des demandes de changement. |

---

## 5. Concepts métier

### 5.1 Produit et Prix

- **Produit** — Entité appartenant à une famille, associée à un ou plusieurs prix.
- **Prix** — Défini au niveau pays ou magasin. Il peut être de type `STANDARD` ou `PROMO`, possède une période de validité et fait l'objet d'un archivage historique.

Lorsqu’un prix existe à la fois au niveau pays et au niveau magasin, le prix magasin constitue une surcharge locale et est appliqué en priorité.


### 5.2 Promotion et Vente

- **Promotion** — Entité temporelle influençant les prix promotionnels au niveau national ou local.
- **Vente** — Transaction réalisée en magasin, liant un produit à un prix et, le cas échéant, à une promotion.

### 5.3 Flux de validation

- **Demande de changement** — Requête portant sur un produit ou un périmètre géographique, soumise à validation avant mise en application.

---

## 6. Règles de gestion

Les règles de gestion ci-dessous sont identifiées par un code unique (`RGxx`) pour assurer leur traçabilité dans le code et les tests.

### 6.1 Périmètre et Organisation

| Règle | Énoncé |
|---|---|
| **RG01** | L'application ne gère que des **magasins physiques**. La notion de canal (online / offline) est hors périmètre. |

### 6.2 Gestion du Pricing

| Règle | Énoncé |
|---|---|
| **RG02** | Un produit peut posséder **plusieurs prix successifs** dans le temps. |
| **RG03** | Un prix est toujours défini pour un pays (`country_id` obligatoire). Le champ `store_id` est optionnel. |
| **RG04** | Un prix peut être défini au niveau **pays** (prix global) ou au niveau **magasin** (prix local spécifique). |
| **RG05** | Tout prix promotionnel doit être **impérativement** associé à une promotion active. |
| **RG06** | La validité d'un prix est encadrée par les champs `effective_from` et `effective_to`. |
| **RG07** | Il ne doit jamais exister plusieurs prix actifs simultanément pour un même produit sur un même périmètre (pays ou magasin) sur une période donnée. |


### 6.3 Gestion des Promotions

| Règle | Énoncé |
|---|---|
| **RG08** | Les promotions sont strictement délimitées par une date de début et une date de fin. |
| **RG08bis** | Pour un produit donné, dans un magasin donné et à une date donnée, le prix applicable est déterminé selon l’ordre de priorité suivant : (1) prix magasin actif, (2) à défaut prix pays actif. |
| **RG09** | Une promotion est définie soit au niveau pays (applicable à tous les magasins du pays), soit au niveau d’un magasin spécifique. || **RG09bis** | Une promotion cible **un seul produit** (`product_id` NOT NULL). Pas de bundle ni de set. |
| **RG09ter** | Le type de remise (`discount_type`) est limité à deux valeurs : `PERCENTAGE` (pourcentage de réduction) ou `FIXED_PRICE` (prix fixe imposé). |
### 6.4 Gestion des Ventes

| Règle | Énoncé |
|---|---|
| **RG10** | Pour chaque vente, la quantité et le montant doivent être **strictement positifs**. |

### 6.5 Workflow et Audit

| Règle | Énoncé |
|---|---|
| **RG11** | L'application d'un nouveau prix est conditionnée par une **validation préalable**. |
| **RG12** | Les statuts d'une demande suivent le cycle : `PENDING` → `APPROVED` → `APPLIED` *(ou `REJECTED` / `FAILED`)*. |
| **RG13** | L'historisation des prix et le journal d'audit (actions utilisateurs) sont **obligatoires**. |

---

## 7. KPI et Analytique

### Structure de données

Utilisation d'une table analytique centrale unique : `obt_sales`.

### Indicateurs de performance

- **Prix** — Comparaison des performances avant/après changement et benchmark par rapport au niveau pays.
- **Promotion** :
  - *Baseline* fixée à **14 jours** avant le début de la promotion.
  - **KPI principal (uplift)** : calculé **uniquement au niveau produit** — même produit AVANT promo vs PENDANT promo. La famille ne doit jamais être utilisée pour ce calcul.
  - **KPI complémentaire (famille)** : variation des ventes des autres produits de la même famille pendant la promo, pour détecter cannibalisation ou effet halo.
  - Mesure de l'accélération (Quantité et CA).

---

## 8. Architecture technique

| Composant | Technologie | Rôle |
|---|---|---|
| **Backend** | FastAPI | Logique métier et exposition API REST |
| **Frontend** | Django / Tailwind CSS | Interface utilisateur et rendu serveur (SSR) |
| **Base de données** | PostgreSQL | Stockage `pct_core` (transac.) et `pct_analytics` (data) |
| **Transformation** | dbt | Pipeline de données pour la table `obt_sales` |
| **Service IA** | Python dédié | Analyse et suggestions en lecture seule |
| **Déploiement** | Docker / GCP Cloud Run | Conteneurisation et hébergement cloud |

---

## 9. Contraintes

- Réalisation en **autonomie complète**.
- Architecture modulaire favorisant la maintenabilité.
- Utilisation de données simulées cohérentes avec le secteur.
- **Interdiction** d'automatisation des décisions de pricing (*humain dans la boucle*).
- Exigence de **traçabilité totale** sur les flux de données et d'actions.

---

## 10. Definition of Done (DoD)

Le projet est considéré comme finalisé après validation des étapes suivantes :

- [ ] Instance PostgreSQL opérationnelle.
- [ ] API FastAPI et application Django fonctionnelles et interconnectées.
- [ ] Calculs analytiques validés via dbt.
- [ ] KPI disponibles et conformes aux règles métier.
- [ ] Service IA opérationnel en lecture seule.
- [ ] Pipeline CI/CD et monitoring configurés.
- [ ] Documentation technique et fonctionnelle exhaustive.
