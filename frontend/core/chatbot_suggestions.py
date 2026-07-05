CHATBOT_SUGGESTIONS_BY_PAGE: dict[str, list[str]] = {
    "dashboard": [
        "Explique le KPI chiffre d'affaires",
        "Quel prix devrais-je revoir en priorité ?",
        "Comment l'assistant aide-t-il aux décisions tarifaires ?",
    ],
    "products": [
        "Liste les produits actifs",
        "Quelles sont les familles de produits ?",
        "Explique-moi les anomalies de prix.",
    ],
    "prices": [
        "Liste des prix du produit 3",
        "Comment fonctionne le workflow de changement de prix ?",
        "Explique les règles de portée des prix",
    ],
    "promotions": [
        "Liste les promotions actives",
        "Comment les promotions sont-elles documentées ?",
        "Le chatbot peut-il approuver une demande de changement de prix ?",
    ],
    "price_change_requests": [
        "Liste les demandes de changement de prix en attente",
        "Comment fonctionne le workflow de changement de prix ?",
        "Le chatbot peut-il approuver une demande de changement de prix ?",
    ],
    "anomalies": [
        "Quelles anomalies dois-je examiner en priorité ?",
        "Quel prix devrais-je revoir en priorité ?",
        "Comment les anomalies sont-elles définies ?",
    ],
    "default": [
        "Que peut faire ce chatbot ?",
        "Quelle est la part des ventes promo ?",
        "Comment fonctionne le workflow de changement de prix ?",
    ],
}


def get_chatbot_suggestions(page_name: str | None) -> list[str]:
    if not page_name:
        return CHATBOT_SUGGESTIONS_BY_PAGE["default"]
    return CHATBOT_SUGGESTIONS_BY_PAGE.get(
        page_name,
        CHATBOT_SUGGESTIONS_BY_PAGE["default"],
    )
