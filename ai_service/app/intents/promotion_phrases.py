"""Phrases for promotion data and promotion clarification intents.

PROMOTIONS_PHRASES — scoped promotion queries that call the promotion tool.
  Bare "show/list promotions" are excluded here and handled as clarify_promotions.
  "produits en promo" is listed explicitly so it cannot fall through to reference_data.

CLARIFY_PROMOTIONS_EXACT — bare promotion commands that need clarification.

CLARIFY_PROMOTION_CONTEXT_PHRASES — vague references to "cette promotion" that
  require the user to specify a promotion ID or product.  Evaluated before the
  documentary knowledge fallback, but after the more specific
  DOCUMENTARY_PROMOTION_DIAGNOSIS_PHRASES (workflow_phrases.py, priority 94)
  so that "pourquoi cette promo ne marche pas ?" gets an answer instead of a
  clarification prompt.

CLARIFY_PROMOTION_PHRASES — vague "tell me about promotion" queries.
"""

PROMOTIONS_PHRASES: list[str] = [
    "produits en promo",
    "produits en promotion",
    "produits promo",
    "products on promotion",
    "promoted products",
    "active promotions",
    "list active promotions",
    "what promotions",
    "available promotions",
    "current promotions",
    "promotions for store",
    "promotions for product",
    "liste des promotions",
    "liste les promotions",
    "promotions actives",
    "quelles promotions",
    "quelles promotions concernent",
    "promotions du magasin",
    "promotions pour le magasin",
    "promotions du produit",
    "promotions pour le produit",
    "quelle promotion a",
    "quelle promotion genere",
    "quelle promotion a le plus",
    "promotion a un mauvais",
]

CLARIFY_PROMOTIONS_EXACT: frozenset[str] = frozenset(
    {"show promotions", "list promotions", "promotions"}
)

CLARIFY_PROMOTION_CONTEXT_PHRASES: list[str] = [
    "cette promotion",
    "cette promo",
    "pourquoi cette promo",
    "pourquoi cette promotion",
    "this promotion",
    "dois-je arreter",
    "dois je arreter",
    "dois-je prolonger cette",
    "dois-je stopper cette",
    "dois je stopper cette",
]

CLARIFY_PROMOTION_PHRASES: list[str] = [
    "tell me about promotion",
]
