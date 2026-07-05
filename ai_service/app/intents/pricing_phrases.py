"""Phrases for KPI, price change request, and price data intents.

KPI_DATA_PHRASES + KPI_DATA_REGEX — live figures from the backend KPI tool.
  Placed BEFORE KPI_EXPLANATION_PHRASES so interrogative data questions ("quel
  est le chiffre…") route to the tool rather than the static explanation service.

DECISION_KPI_PHRASES — kept in decision_phrases.py (imported here for reference).

KPI_EXPLANATION_PHRASES — conceptual KPI definitions.

PRICE_CHANGE_REQUEST_PHRASES — price change request listing.

PRICES_PHRASES — direct price data queries.

Clarification constants:
  CLARIFY_PRICES_EXACT — bare price commands requiring clarification.
  CLARIFY_PRICE_REQUESTS_EXACT — bare request commands requiring clarification.
"""

KPI_DATA_PHRASES: list[str] = [
    # French interrogative forms requesting a current value
    "quel est le chiffre",
    "quel est le ca",
    "quelle est la marge",
    "quel est le volume vendu",
    "quel est le volume",
    "quel est le panier moyen",
    "quel est le panier",
    "quelle est la part des ventes",
    "quelle est la part du ca",
    "quelle est la part promo",
    "quel est le revenu",
    # English interrogative forms
    "what is the revenue",
    "what is the total revenue",
    "what is the margin",
    "what is the volume",
    "how much revenue",
    "how much margin",
    # Aggregate / scoped phrases
    "total revenue",
    "revenue for store",
    "revenue for product",
    "margin for store",
    "margin for product",
    "country revenue",
    "chiffre d'affaires total",
    # Revenue synonyms
    "sales amount",
    "turnover",
]

# "\bca\b" matches the French acronym "CA" (chiffre d'affaires) with word
# boundaries so that "can you…" is never caught by this pattern.
KPI_DATA_REGEX: list[str] = [r"\bca\b"]

KPI_EXPLANATION_PHRASES: list[str] = [
    "kpi",
    "indicator",
    "metric",
    "margin",
    "marge",
    "volume",
    "performance",
    "explain kpi",
    "explique le kpi",
    "uplift",
    "panier moyen",
    "average order value",
    "average basket",
    "discount rate",
    "taux de remise",
    "chiffre d'affaires",
    "chiffre d affaires",
    "part des ventes",
    "part des ventes promo",
    "promo share",
    "promotion sales share",
    "comment est calcule",
    "comment interpreter",
    "qu'est-ce que le",
    "qu est ce que le",
    "definition chiffre",
    "price gap",
    "what does revenue",
    "what does margin",
    "what does volume",
    # French KPI explanation triggers — apostrophe-agnostic substrings
    "explique le chiffre",
    "expliquer le chiffre",
    "explique le ca",
    "explique la marge",
    "explique le volume",
    "explique le panier",
    "explique l'uplift",
    "explique l uplift",
    "explique la part",
    "qu est-ce que le",
]

PRICE_CHANGE_REQUEST_PHRASES: list[str] = [
    "list price changes",
    "show price changes",
    "price changes for store",
    "price change history",
    "price change request",
    "change requests",
    "price requests",
    "pending price",
    "approved price",
    "waiting for approval",
    "historique prix",
    "liste des changements de prix",
    "demandes de changement de prix",
    "demandes de prix",
    "demandes pending",
    "demandes en attente",
    "demandes approved",
    "demandes approuvees",
    "demandes validees",
    "demandes rejected",
    "demandes rejetees",
    "demandes refusees",
    "approved requests",
    "rejected requests",
]

PRICES_PHRASES: list[str] = [
    "quel est le prix de",
    "price of",
    "what is the price of",
    "prices for product",
    "prices for store",
    "liste des prix",
    "quels prix",
    "prix du produit",
    "prix du magasin",
    "prix actifs",
    "prix actif",
    "quel est le prix du",
    "quel est le prix actuel",
    "quels produits ont un prix",
]

# Exact-match sets for bare price/request commands that need clarification
CLARIFY_PRICES_EXACT: frozenset[str] = frozenset(
    {"show prices", "list prices", "what prices", "explain price", "prix"}
)
CLARIFY_PRICE_REQUESTS_EXACT: frozenset[str] = frozenset(
    {"show requests", "list requests"}
)
