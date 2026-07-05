"""Response dispatcher.

Routes an IntentMatch to the correct specialized handler based on its
RouteType.  The dispatcher itself contains no business logic — it is a
pure routing switch between the handler layer and the orchestrator.
"""

from typing import Any

from app.core.chatbot_messages import (
    CHATBOT_NOT_IMPLEMENTED_MESSAGE,
    CHATBOT_UNSUPPORTED_USE_CASE_MESSAGE,
)
from app.handlers.clarification_handler import ClarificationHandler
from app.handlers.guardrail_handler import GuardrailHandler
from app.handlers.rag_response_handler import RAGResponseHandler
from app.handlers.static_response_handler import StaticResponseHandler
from app.handlers.tool_response_handler import ToolResponseHandler
from app.orchestrator.chat_context import ChatContext
from app.orchestrator.intent_types import IntentMatch, RouteType
from app.services.response_generation_service import ResponseGenerationService


class ResponseDispatcher:
    def __init__(
        self,
        static_handler: StaticResponseHandler,
        guardrail_handler: GuardrailHandler,
        clarification_handler: ClarificationHandler,
        tool_handler: ToolResponseHandler,
        rag_handler: RAGResponseHandler,
        response_service: ResponseGenerationService,
    ) -> None:
        self._static = static_handler
        self._guardrail = guardrail_handler
        self._clarification = clarification_handler
        self._tool = tool_handler
        self._rag = rag_handler
        self._response_service = response_service

    def dispatch(self, ctx: ChatContext, match: IntentMatch) -> dict[str, Any]:
        route_type = match.route_type

        if route_type == RouteType.UNSUPPORTED:
            return {
                "status": "unsupported",
                "answer": self._response_service.format_fallback_response(lang=ctx.lang),
                "source": "orchestrator",
                "message": CHATBOT_UNSUPPORTED_USE_CASE_MESSAGE,
            }

        if route_type == RouteType.GUARDRAIL:
            return self._guardrail.handle(ctx, match)

        if route_type == RouteType.STATIC:
            return self._static.handle(ctx, match)

        if route_type == RouteType.CLARIFICATION:
            return self._clarification.handle(ctx, match)

        if route_type == RouteType.TOOL:
            return self._tool.handle(ctx, match)

        if route_type == RouteType.RAG:
            return self._rag.handle(ctx, match)

        return {
            "status": "not_implemented",
            "answer": CHATBOT_NOT_IMPLEMENTED_MESSAGE,
            "source": "orchestrator",
        }
