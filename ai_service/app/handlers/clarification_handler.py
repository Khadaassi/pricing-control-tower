"""Handler for clarification responses.

When the router detects an intent that cannot be resolved without additional
context (bare "show prices", vague "cette promotion"…), this handler returns
a structured clarification message without calling any tool.

The per-language message dictionaries mirror the original orchestrator mapping
so that the correct bilingual message is always selected.
"""

from typing import Any

from app.core.chatbot_messages import (
    CHATBOT_GENERIC_RECOMMENDATION_CLARIFICATION_MESSAGE,
    CHATBOT_GENERIC_RECOMMENDATION_CLARIFICATION_MESSAGE_EN,
    CHATBOT_PRICE_CLARIFICATION_MESSAGE,
    CHATBOT_PRICE_CLARIFICATION_MESSAGE_FR,
    CHATBOT_PRICE_REQUEST_CLARIFICATION_MESSAGE,
    CHATBOT_PRICE_REQUEST_CLARIFICATION_MESSAGE_EN,
    CHATBOT_PRODUCT_CLARIFICATION_MESSAGE,
    CHATBOT_PRODUCT_CLARIFICATION_MESSAGE_EN,
    CHATBOT_PROMOTION_CLARIFICATION_MESSAGE,
    CHATBOT_PROMOTION_CLARIFICATION_MESSAGE_EN,
    CHATBOT_PROMOTION_CONTEXT_CLARIFICATION_MESSAGE,
    CHATBOT_PROMOTION_CONTEXT_CLARIFICATION_MESSAGE_EN,
    CHATBOT_STORE_CLARIFICATION_MESSAGE,
    CHATBOT_STORE_CLARIFICATION_MESSAGE_FR,
)
from app.orchestrator.chat_context import ChatContext
from app.orchestrator.intent_types import IntentMatch
from app.services.response_generation_service import ResponseGenerationService

_CLARIFICATION_MESSAGES_FR: dict[str, str | None] = {
    "clarify_prices": CHATBOT_PRICE_CLARIFICATION_MESSAGE_FR,
    "clarify_promotions": CHATBOT_PROMOTION_CLARIFICATION_MESSAGE,
    "clarify_promotion_context": CHATBOT_PROMOTION_CONTEXT_CLARIFICATION_MESSAGE,
    "clarify_store": CHATBOT_STORE_CLARIFICATION_MESSAGE_FR,
    "clarify_product": CHATBOT_PRODUCT_CLARIFICATION_MESSAGE,
    "clarify_price_requests": CHATBOT_PRICE_REQUEST_CLARIFICATION_MESSAGE,
    "generic_recommendation_clarification": CHATBOT_GENERIC_RECOMMENDATION_CLARIFICATION_MESSAGE,
    "ambiguous_question": None,
}

_CLARIFICATION_MESSAGES_EN: dict[str, str | None] = {
    "clarify_prices": CHATBOT_PRICE_CLARIFICATION_MESSAGE,
    "clarify_promotions": CHATBOT_PROMOTION_CLARIFICATION_MESSAGE_EN,
    "clarify_promotion_context": CHATBOT_PROMOTION_CONTEXT_CLARIFICATION_MESSAGE_EN,
    "clarify_store": CHATBOT_STORE_CLARIFICATION_MESSAGE,
    "clarify_product": CHATBOT_PRODUCT_CLARIFICATION_MESSAGE_EN,
    "clarify_price_requests": CHATBOT_PRICE_REQUEST_CLARIFICATION_MESSAGE_EN,
    "generic_recommendation_clarification": CHATBOT_GENERIC_RECOMMENDATION_CLARIFICATION_MESSAGE_EN,
    "ambiguous_question": None,
}


class ClarificationHandler:
    def __init__(self, response_service: ResponseGenerationService) -> None:
        self._response_service = response_service

    def handle(self, ctx: ChatContext, match: IntentMatch) -> dict[str, Any]:
        lang = ctx.lang
        messages = _CLARIFICATION_MESSAGES_FR if lang == "fr" else _CLARIFICATION_MESSAGES_EN
        message = messages.get(match.intent.value)

        return {
            "status": "clarification",
            "answer": self._response_service.format_clarification_response(message, lang=lang),
            "source": "orchestrator",
        }
