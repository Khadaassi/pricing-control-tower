"""Lightweight chatbot orchestrator.

Responsibilities:
  1. Build a ChatContext from the raw request parameters.
  2. Call IntentRouter to obtain a deterministic IntentMatch.
  3. Call ResponseDispatcher to route the match to the correct handler.
  4. Return a uniform response dict.

The orchestrator no longer contains phrase lists, routing if/elif chains,
response formatting logic, or tool invocation code.  All of those concerns
live in the specialized modules:

  app/orchestrator/intent_router.py   — deterministic intent detection
  app/orchestrator/intent_registry.py — declarative routing rules
  app/orchestrator/response_dispatcher.py — handler dispatch
  app/handlers/*                      — specialized response handlers
  app/intents/*                       — intent phrase constants
"""

from typing import Any

from app.core.chatbot_messages import CHATBOT_UNSUPPORTED_USE_CASE_MESSAGE
from app.core.language_detector import detect_language
from app.core.logging_config import get_logger, log_event
from app.core.metrics import increment_chat_tool_usage_total
from app.handlers.clarification_handler import ClarificationHandler
from app.handlers.guardrail_handler import GuardrailHandler
from app.handlers.rag_response_handler import RAGResponseHandler, RAG_FALLBACK_ANSWER
from app.handlers.static_response_handler import StaticResponseHandler
from app.handlers.tool_response_handler import ToolResponseHandler
from app.llm.base import BaseLLMProvider
from app.llm.factory import get_llm_provider
from app.orchestrator.chat_context import ChatContext
from app.orchestrator.intent_types import Intent, RouteType
from app.orchestrator.intent_router import IntentRouter
from app.orchestrator.normalization import normalize
from app.orchestrator.response_dispatcher import ResponseDispatcher
from app.rag.prompt_builder import RAGPromptBuilder
from app.rag.retriever import DocumentRetriever
from app.services.business_rules_explanation_service import BusinessRulesExplanationService
from app.services.kpi_explanation_service import KPIExplanationService
from app.services.rbac_explanation_service import RBACExplanationService
from app.services.response_generation_service import ResponseGenerationService
from app.tools.anomaly_tool import AnomalyTool
from app.tools.kpi_data_tool import KPIDataTool
from app.tools.price_change_request_tool import PriceChangeRequestTool
from app.tools.price_tool import PriceTool
from app.tools.promotion_tool import PromotionTool
from app.tools.reference_data_tool import ReferenceDataTool

logger = get_logger("ai_service.orchestrator")

# Re-exported for backward compatibility with existing tests and code that
# import _RAG_FALLBACK_ANSWER directly from this module.
_RAG_FALLBACK_ANSWER = RAG_FALLBACK_ANSWER

# Maps intent → selected_tool name returned in route_question() response.
# "none" is expressed as None; RAG and static responses have no selected_tool.
_TOOL_BY_INTENT: dict[str, str | None] = {
    Intent.GET_KPI_DATA: "kpi_data_tool",
    Intent.LIST_ANOMALIES: "anomaly_tool",
    Intent.EXPLAIN_ANOMALY_DEFINITION: "anomaly_tool",
    Intent.LIST_STORE_PRICE_CHANGES: "price_change_request_tool",
    Intent.LIST_STORE_COUNTRY_PRICE_MISMATCHES: "anomaly_tool",
    Intent.EXPLAIN_KPI: "kpi_explanation_tool",
    Intent.EXPLAIN_BUSINESS_RULE: "business_rules_tool",
    Intent.EXPLAIN_RBAC: "rbac_tool",
    Intent.PROMOTIONS: "promotion_tool",
    Intent.PRICES: "price_tool",
    Intent.REFERENCE_DATA: "reference_data_tool",
    Intent.DOCUMENTARY_KNOWLEDGE: "rag_retriever",
    Intent.GUARDRAIL: None,
    Intent.CHATBOT_LIMITS: None,
    Intent.CHATBOT_CAPABILITIES: None,
    Intent.DECISION_KPI_GUIDANCE: None,
    Intent.AMBIGUOUS_QUESTION: None,
    Intent.CLARIFY_PRICES: None,
    Intent.CLARIFY_PROMOTIONS: None,
    Intent.CLARIFY_PROMOTION_CONTEXT: None,
    Intent.CLARIFY_STORE: None,
    Intent.CLARIFY_PRODUCT: None,
    Intent.CLARIFY_PRICE_REQUESTS: None,
    Intent.GENERIC_RECOMMENDATION_CLARIFICATION: None,
}


class ChatbotOrchestrator:
    """Lightweight orchestrator: context → router → dispatcher → response."""

    def __init__(
        self,
        business_rules_service: BusinessRulesExplanationService | None = None,
        rbac_service: RBACExplanationService | None = None,
        anomaly_tool: AnomalyTool | None = None,
        kpi_service: KPIExplanationService | None = None,
        kpi_data_tool: KPIDataTool | None = None,
        price_change_request_tool: PriceChangeRequestTool | None = None,
        promotion_tool: PromotionTool | None = None,
        price_tool: PriceTool | None = None,
        reference_data_tool: ReferenceDataTool | None = None,
        document_retriever: DocumentRetriever | None = None,
        llm_provider: BaseLLMProvider | None = None,
        response_service: ResponseGenerationService | None = None,
    ) -> None:
        _business_rules_service = business_rules_service or BusinessRulesExplanationService()
        _rbac_service = rbac_service or RBACExplanationService()
        _anomaly_tool = anomaly_tool or AnomalyTool()
        _kpi_service = kpi_service or KPIExplanationService()
        _kpi_data_tool = kpi_data_tool or KPIDataTool()
        _price_change_request_tool = price_change_request_tool or PriceChangeRequestTool()
        _promotion_tool = promotion_tool or PromotionTool()
        _price_tool = price_tool or PriceTool()
        _reference_data_tool = reference_data_tool or ReferenceDataTool()
        _document_retriever = document_retriever or DocumentRetriever()
        _llm_provider = llm_provider or get_llm_provider()
        _response_service = response_service or ResponseGenerationService()
        _prompt_builder = RAGPromptBuilder()

        self._router = IntentRouter()

        _static_handler = StaticResponseHandler(response_service=_response_service)
        _guardrail_handler = GuardrailHandler(response_service=_response_service)
        _clarification_handler = ClarificationHandler(response_service=_response_service)
        _tool_handler = ToolResponseHandler(
            business_rules_service=_business_rules_service,
            rbac_service=_rbac_service,
            anomaly_tool=_anomaly_tool,
            kpi_service=_kpi_service,
            kpi_data_tool=_kpi_data_tool,
            price_change_request_tool=_price_change_request_tool,
            promotion_tool=_promotion_tool,
            price_tool=_price_tool,
            reference_data_tool=_reference_data_tool,
            response_service=_response_service,
        )
        _rag_handler = RAGResponseHandler(
            document_retriever=_document_retriever,
            llm_provider=_llm_provider,
            prompt_builder=_prompt_builder,
            response_service=_response_service,
        )
        self._dispatcher = ResponseDispatcher(
            static_handler=_static_handler,
            guardrail_handler=_guardrail_handler,
            clarification_handler=_clarification_handler,
            tool_handler=_tool_handler,
            rag_handler=_rag_handler,
            response_service=_response_service,
        )

    # ------------------------------------------------------------------
    # Public API (preserved for backward compatibility)
    # ------------------------------------------------------------------

    def route_question(self, question: str) -> dict[str, Any]:
        """Return routing metadata without executing any tool or LLM call."""
        match = self._router.route(question)
        selected_tool = _TOOL_BY_INTENT.get(match.intent)

        if match.route_type == RouteType.UNSUPPORTED:
            return {
                "question": question,
                "intent": match.intent.value,
                "selected_tool": None,
                "status": "unsupported",
                "message": CHATBOT_UNSUPPORTED_USE_CASE_MESSAGE,
            }

        return {
            "question": question,
            "intent": match.intent.value,
            "selected_tool": selected_tool,
            "status": "routed",
        }

    def answer_question(
        self,
        question: str,
        user_email: str | None = None,
        store_id: int | None = None,
    ) -> dict[str, Any]:
        """Route and answer a question, returning a uniform response dict."""
        lang = detect_language(question)
        ctx = ChatContext(
            original_question=question,
            normalized_question=normalize(question),
            user_email=user_email,
            store_id=store_id,
            lang=lang,
        )

        match = self._router.route(question)
        tool_name = _TOOL_BY_INTENT.get(match.intent) or "none"

        log_event(
            logger,
            "chat_tool_selected",
            intent=match.intent.value,
            tool_name=tool_name,
            user_email_present=user_email is not None,
            store_id_present=store_id is not None,
        )
        increment_chat_tool_usage_total(tool_name)

        handler_result = self._dispatcher.dispatch(ctx, match)

        return {
            "question": question,
            "intent": match.intent.value,
            "selected_tool": _TOOL_BY_INTENT.get(match.intent),
            **handler_result,
        }

    # ------------------------------------------------------------------
    # Internal context builder (kept for potential subclass use)
    # ------------------------------------------------------------------

    def _build_context(
        self,
        question: str,
        user_email: str | None = None,
        store_id: int | None = None,
    ) -> ChatContext:
        return ChatContext(
            original_question=question,
            normalized_question=normalize(question),
            user_email=user_email,
            store_id=store_id,
            lang=detect_language(question),
        )
