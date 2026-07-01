CHATBOT_SUGGESTIONS_BY_PAGE: dict[str, list[str]] = {
    "dashboard": [
        "Explain the revenue KPI",
        "What anomalies should I review first?",
        "How does the chatbot help with pricing decisions?",
    ],
    "products": [
        "List active products",
        "Show product families",
        "What about product 3?",
    ],
    "prices": [
        "List prices for product 3",
        "How does the price change workflow work?",
        "Explain price scope rules",
    ],
    "promotions": [
        "List active promotions",
        "How are promotions documented?",
        "Can the chatbot approve a price change?",
    ],
    "price_change_requests": [
        "List pending price change requests",
        "How does the price change workflow work?",
        "Can the chatbot approve a price change?",
    ],
    "anomalies": [
        "Show anomalies for store 1",
        "How are anomalies defined?",
        "What should I review first?",
    ],
    "default": [
        "What can the chatbot do?",
        "Explain store manager permissions",
        "How does the price change workflow work?",
    ],
}


def get_chatbot_suggestions(page_name: str | None) -> list[str]:
    if not page_name:
        return CHATBOT_SUGGESTIONS_BY_PAGE["default"]
    return CHATBOT_SUGGESTIONS_BY_PAGE.get(
        page_name,
        CHATBOT_SUGGESTIONS_BY_PAGE["default"],
    )
