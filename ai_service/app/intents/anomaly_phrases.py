"""Phrases and constants for anomaly-related intents.

Routing priority within anomaly detection (preserved from original logic):
  1. ANOMALY_DEFINITION_PHRASES   — explain a specific anomaly type (no data call)
  2. PRICE_TYPE_ANOMALY_PHRASES   — price-type queries without requiring store_id
  3. PRICE_MISMATCH_PHRASES       — store-vs-country price queries (requires store_id)
  4. GENERAL_ANOMALY_PHRASES      — all anomaly types; covers margin/promo sub-questions

Sub-classification constants (used by ToolResponseHandler, not by the router):
  PRICE_REVIEW_PHRASES, MARGIN_IMPACT_PHRASES, PROMO_ANALYSIS_PHRASES,
  CRITICAL_ANOMALY_PHRASES, PRICE_REVIEW_ANOMALY_TYPES, PROMO_MARGIN_ANOMALY_TYPES,
  CRITICAL_ANOMALY_PRIORITY, ANOMALY_SEVERITY, ANOMALY_DEFINITION_TEXTS.
"""

ANOMALY_DEFINITION_PHRASES: list[str] = [
    "explique price_above_reference",
    "explain price_above_reference",
    "explique underperforming_promo",
    "explain underperforming_promo",
    "explique ineffective_discount",
    "explain ineffective_discount",
    "explique inter_store_price_gap",
    "explain inter_store_price_gap",
]

PRICE_TYPE_ANOMALY_PHRASES: list[str] = [
    # PRICE_ABOVE_REFERENCE
    "produits sont au dessus du prix conseille",
    "produits au dessus du prix conseille",
    "prix au dessus du prix conseille",
    "prix conseille",
    "au-dessus du prix conseille",
    # English
    "price above reference",
    # INTER_STORE_PRICE_GAP
    "magasins ont un ecart de prix",
    "ecart de prix entre magasins",
    "ecart de prix",
]

PRICE_MISMATCH_PHRASES: list[str] = [
    "mismatch",
    "price mismatch",
    "country price",
    "store price",
    "above reference",
    "price above",
    "prix pays",
    "prix magasin",
    "ecart de prix",
    "prix non aligne",
    "price_above_reference",
]

GENERAL_ANOMALY_PHRASES: list[str] = [
    "anomaly",
    "anomalies",
    "anomalie",
    "liste les anomalies",
    "quelles anomalies",
    "anomalies critiques",
    "underperforming",
    "ineffective discount",
    "est inefficace",
    "promotion sous-performante",
    "inter_store_price_gap",
    "quelle promotion est inefficace",
    "quelle promo est inefficace",
    # Prioritisation requests
    "quel prix devrais je revoir",
    "quel prix devrais-je revoir",
    "quel prix dois je revoir",
    "quel prix dois-je revoir",
    "prix a revoir en priorite",
    "quel prix revoir en priorite",
    "prix devrais je revoir",
    "prix dois je revoir",
    "prix dois-je revoir",
    "prioriser les prix",
    "prix prioritaire",
    # Margin impact promotion phrases — must precede explain_kpi ("marge")
    "mauvais impact marge",
    "impact marge negatif",
    "promotion degrade la marge",
    "degrade la marge",
    "bad margin impact",
    "promotion margin issue",
    "impact negatif sur la marge",
    "promotion a un mauvais impact",
    "promotion qui degrade",
    # Promotion analysis / prioritisation phrases
    "quelle promotion dois-je analyser",
    "quelle promotion dois je analyser",
    "promotion a analyser",
    "promotion prioritaire",
    "quelle promo regarder",
    "quelle promo analyser",
    "quelle promo dois-je",
    "quelle promo dois je",
]

# --- Sub-classification constants (used by ToolResponseHandler) ---

PRICE_REVIEW_PHRASES: tuple[str, ...] = (
    "prix devrais je revoir",
    "prix devrais-je revoir",
    "prix dois je revoir",
    "prix dois-je revoir",
    "prix a revoir",
    "prix revoir en priorite",
    "quel prix revoir",
    "quel prix devrais je revoir",
    "quel prix devrais-je revoir",
    "quel prix dois je revoir",
    "quel prix dois-je revoir",
    "prioriser les prix",
    "prix prioritaire",
    "price to review",
    "price should i review",
)

MARGIN_IMPACT_PHRASES: tuple[str, ...] = (
    "mauvais impact marge",
    "impact marge negatif",
    "promotion degrade la marge",
    "degrade la marge",
    "bad margin impact",
    "promotion margin issue",
    "impact negatif sur la marge",
    "promotion a un mauvais impact",
    "promotion qui degrade",
)

PROMO_ANALYSIS_PHRASES: tuple[str, ...] = (
    "quelle promotion dois-je analyser",
    "quelle promotion dois je analyser",
    "promotion a analyser",
    "promotion prioritaire",
    "quelle promo regarder",
    "quelle promo analyser",
    "quelle promo dois-je",
    "quelle promo dois je",
)

CRITICAL_ANOMALY_PHRASES: tuple[str, ...] = (
    "anomalies critiques",
    "anomalies prioritaires",
    "anomalies les plus critiques",
    "anomalies les plus importantes",
    "sont critiques",
    "les plus critiques",
    "les plus urgentes",
    "critical anomalies",
    "priority anomalies",
    "most critical",
    "highest priority",
)

PRICE_REVIEW_ANOMALY_TYPES: frozenset[str] = frozenset(
    {"PRICE_ABOVE_REFERENCE", "INTER_STORE_PRICE_GAP"}
)

PROMO_MARGIN_ANOMALY_TYPES: frozenset[str] = frozenset(
    {"INEFFECTIVE_DISCOUNT", "UNDERPERFORMING_PROMO"}
)

CRITICAL_ANOMALY_PRIORITY: list[str] = [
    "PRICE_ABOVE_REFERENCE",
    "INEFFECTIVE_DISCOUNT",
    "UNDERPERFORMING_PROMO",
    "INTER_STORE_PRICE_GAP",
]

ANOMALY_SEVERITY: dict[str, str] = {
    "PRICE_ABOVE_REFERENCE": "CRITICAL",
    "INEFFECTIVE_DISCOUNT": "HIGH",
    "UNDERPERFORMING_PROMO": "MEDIUM",
    "INTER_STORE_PRICE_GAP": "MEDIUM",
}

ANOMALY_DEFINITION_TEXTS: dict[str, dict] = {
    "PRICE_ABOVE_REFERENCE": {
        "fr": {
            "summary": "PRICE_ABOVE_REFERENCE signifie que le prix magasin est supérieur au prix de référence pays.",
            "details": [
                "Cela peut créer une incohérence prix pour le client.",
                "L'écart doit être vérifié avant toute action.",
                "Le prix ne doit pas être modifié automatiquement.",
            ],
            "next_step": "Comparez le prix magasin au prix pays et vérifiez si l'écart est justifié localement.",
        },
        "en": {
            "summary": "PRICE_ABOVE_REFERENCE means the store price is higher than the country reference price.",
            "details": [
                "This may create price inconsistency for customers.",
                "The gap must be verified before any action.",
                "The price must not be changed automatically.",
            ],
            "next_step": "Compare the store price with the country reference price and verify if the gap is justified locally.",
        },
    },
    "UNDERPERFORMING_PROMO": {
        "fr": {
            "summary": "UNDERPERFORMING_PROMO signifie que la promotion génère des performances inférieures aux attentes.",
            "details": [
                "La promotion n'attire pas suffisamment de ventes supplémentaires.",
                "Cela peut indiquer un mauvais ciblage ou une remise insuffisante.",
                "Elle doit être analysée avant d'être prolongée ou arrêtée.",
            ],
            "next_step": "Vérifiez la période, le niveau de remise et la tendance des ventes avant et pendant la promotion.",
        },
        "en": {
            "summary": "UNDERPERFORMING_PROMO means the promotion generates weaker performance than expected.",
            "details": [
                "The promoted product did not attract enough additional sales.",
                "This may indicate poor targeting or insufficient discount.",
                "It should be analyzed before extending or stopping it.",
            ],
            "next_step": "Review the promotion period, discount level, and sales trend before and during the promotion.",
        },
    },
    "INEFFECTIVE_DISCOUNT": {
        "fr": {
            "summary": "INEFFECTIVE_DISCOUNT signifie que la remise ne produit pas d'impact métier significatif.",
            "details": [
                "La réduction de prix peut être trop faible, mal ciblée ou appliquée à un produit peu demandé.",
                "L'impact sur les ventes, le chiffre d'affaires ou la marge est insuffisant.",
                "Vérifiez si la remise a augmenté le volume ou la marge.",
            ],
            "next_step": "Vérifiez si la remise a augmenté le volume des ventes, le CA ou la marge par rapport à la baseline attendue.",
        },
        "en": {
            "summary": "INEFFECTIVE_DISCOUNT means the discount does not produce a meaningful business impact.",
            "details": [
                "The price reduction may be too low, poorly targeted, or applied to a product with limited demand.",
                "The impact on sales, revenue, or margin is insufficient.",
                "Check whether the discount increased sales volume, revenue, or margin.",
            ],
            "next_step": "Check whether the discount increased sales volume, revenue, or margin compared with the expected baseline.",
        },
    },
    "INTER_STORE_PRICE_GAP": {
        "fr": {
            "summary": "INTER_STORE_PRICE_GAP signifie que le prix d'un produit diffère significativement entre magasins.",
            "details": [
                "L'écart de prix peut indiquer une incohérence tarifaire locale.",
                "Il doit être vérifié avant toute action corrective.",
                "Une règle métier locale peut justifier l'écart.",
            ],
            "next_step": "Comparez le prix du magasin avec les autres magasins et vérifiez si l'écart est justifié par une règle locale.",
        },
        "en": {
            "summary": "INTER_STORE_PRICE_GAP means a product price differs significantly across stores.",
            "details": [
                "The price gap may indicate a local pricing inconsistency.",
                "It must be verified before any corrective action.",
                "A local business rule may justify the gap.",
            ],
            "next_step": "Compare the store price with other stores and check whether the gap is explained by a local business rule.",
        },
    },
}
