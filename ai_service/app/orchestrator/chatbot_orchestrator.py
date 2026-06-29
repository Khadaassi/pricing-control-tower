import re
from typing import Any

from app.services.business_rules_explanation_service import (
    BusinessRulesExplanationService,
)
from app.services.rbac_explanation_service import RBACExplanationService
from app.services.kpi_explanation_service import KPIExplanationService
from app.tools.anomaly_tool import AnomalyTool
from app.core.chatbot_messages import (
    CHATBOT_MISSING_STORE_ID_MESSAGE,
    CHATBOT_MISSING_USER_EMAIL_MESSAGE,
    CHATBOT_NOT_IMPLEMENTED_MESSAGE,
    CHATBOT_SUPPORTED_SCOPE_MESSAGE,
    CHATBOT_TECHNICAL_ERROR_MESSAGE,
    CHATBOT_UNSUPPORTED_USE_CASE_MESSAGE,
)
from app.core.logging_config import get_logger, log_event
from app.core.metrics import increment_chat_tool_usage_total

logger = get_logger("ai_service.orchestrator")


class ChatbotOrchestrator:
    def __init__(
        self,
        business_rules_service: BusinessRulesExplanationService | None = None,
        rbac_service: RBACExplanationService | None = None,
        anomaly_tool: AnomalyTool | None = None,
        kpi_service: KPIExplanationService | None = None,
    ) -> None:
        self.business_rules_service = (
            business_rules_service or BusinessRulesExplanationService()
        )
        self.rbac_service = rbac_service or RBACExplanationService()
        self.anomaly_tool = anomaly_tool or AnomalyTool()
        self.kpi_service = kpi_service or KPIExplanationService()

    def route_question(self, question: str) -> dict[str, Any]:
        intent = self._detect_intent(question)
        selected_tool = self._select_tool(intent)

        if intent == "unknown":
            return {
                "question": question,
                "intent": intent,
                "selected_tool": None,
                "status": "unsupported",
                "message": CHATBOT_UNSUPPORTED_USE_CASE_MESSAGE,
            }

        return {
            "question": question,
            "intent": intent,
            "selected_tool": selected_tool,
            "status": "routed",
        }

    def answer_question(
        self,
        question: str,
        user_email: str | None = None,
        store_id: int | None = None,
    ) -> dict[str, Any]:
        routed = self.route_question(question)
        tool_name = routed["selected_tool"] or "none"

        log_event(
            logger,
            "chat_tool_selected",
            intent=routed["intent"],
            tool_name=tool_name,
            user_email_present=user_email is not None,
            store_id_present=store_id is not None,
        )
        increment_chat_tool_usage_total(tool_name)

        if routed["status"] == "unsupported":
            return {
                **routed,
                "answer": CHATBOT_SUPPORTED_SCOPE_MESSAGE,
                "source": "orchestrator",
            }

        intent = routed["intent"]

        if intent == "explain_business_rule":
            try:
                service_response = self.business_rules_service.explain(question)
                return {
                    **routed,
                    **service_response,
                }
            except Exception as error:
                return self._build_error_response(routed, error)

        if intent == "explain_rbac":
            try:
                service_response = self.rbac_service.explain(question)
                return {
                    **routed,
                    **service_response,
                }
            except Exception as error:
                return self._build_error_response(routed, error)

        if intent == "list_store_country_price_mismatches":
            if not user_email:
                return {
                    **routed,
                    "status": "missing_context",
                    "answer": CHATBOT_MISSING_USER_EMAIL_MESSAGE,
                    "source": "orchestrator",
                }

            if store_id is None:
                return {
                    **routed,
                    "status": "missing_context",
                    "answer": CHATBOT_MISSING_STORE_ID_MESSAGE,
                    "source": "orchestrator",
                }

            try:
                anomalies = self.anomaly_tool.list_store_country_price_mismatches(
                    user_email=user_email,
                    store_id=store_id,
                )

                return {
                    **routed,
                    "status": "answered",
                    "answer": anomalies,
                    "source": "anomaly_tool",
                }
            except Exception as error:
                return self._build_error_response(routed, error)
            
        if intent == "explain_kpi":
            try:
                service_response = self.kpi_service.explain(question)
                return {
                    **routed,
                    **service_response,
                }
            except Exception as error:
                return self._build_error_response(routed, error)

        return {
            **routed,
            "status": "not_implemented",
            "answer": CHATBOT_NOT_IMPLEMENTED_MESSAGE,
            "source": "orchestrator",
        }

    def _detect_intent(self, question: str) -> str:
        normalized_question = question.lower()

        # 1. RBAC questions must be detected before KPI/revenue.
        if self._contains_any_phrase(
            normalized_question,
            [
                "rbac",
                "role",
                "roles",
                "permission",
                "permissions",
                "scope",
                "access",
                "rights",
                "store manager",
                "store director",
                "country director",
                "pricing analyst",
                "another store",
                "another country",
            ],
        ):
            return "explain_rbac"

        # 2. Business rules and chatbot limitations.
        if self._contains_any_phrase(
            normalized_question,
            [
                "business rule",
                "rule",
                "workflow",
                "audit",
                "traceability",
                "approve a price change",
                "reject a price change",
                "apply a price change",
                "chatbot approve",
                "chatbot update",
                "chatbot modify",
                "règle métier",
                "règle",
                "traçabilité",
            ],
        ):
            return "explain_business_rule"

        # 3. Price mismatch / anomaly use case.
        if self._contains_any_phrase(
            normalized_question,
            [
                "mismatch",
                "price mismatch",
                "country price",
                "store price",
                "above reference",
                "price above",
                "prix pays",
                "prix magasin",
                "écart de prix",
                "prix non aligné",
                "anomaly",
                "anomalies",
            ],
        ):
            return "list_store_country_price_mismatches"

        # 4. Price change data use case.
        if self._contains_any_phrase(
            normalized_question,
            [
                "list price changes",
                "show price changes",
                "price changes for store",
                "price change history",
                "change requests",
                "price requests",
                "historique prix",
                "liste des changements de prix",
                "demandes de changement de prix",
            ],
        ):
            return "list_store_price_changes"

        # 5. KPI explanation.
        if self._contains_any_phrase(
            normalized_question,
            [
                "kpi",
                "indicator",
                "metric",
                "margin",
                "volume",
                "performance",
                "explain kpi",
            ],
        ):
            return "explain_kpi"

        # 6. Revenue / sales KPI.
        if self._contains_revenue_intent(normalized_question):
            return "get_country_revenue"

        return "unknown"

    def _select_tool(self, intent: str) -> str | None:
        tool_by_intent = {
            "get_country_revenue": "kpi_tool",
            "list_store_price_changes": "price_change_tool",
            "list_store_country_price_mismatches": "anomaly_tool",
            "explain_kpi": "kpi_explanation_tool",
            "explain_business_rule": "business_rules_tool",
            "explain_rbac": "rbac_tool",
        }

        return tool_by_intent.get(intent)

    def _contains_any_phrase(self, text: str, keywords: list[str]) -> bool:
        return any(keyword in text for keyword in keywords)

    def _contains_revenue_intent(self, text: str) -> bool:
        revenue_phrases = [
            "revenue",
            "sales amount",
            "turnover",
            "country revenue",
            "chiffre d'affaires",
        ]

        if self._contains_any_phrase(text, revenue_phrases):
            return True

        # Avoid matching "ca" inside "can".
        return bool(re.search(r"\bca\b", text))

    def _build_error_response(
        self,
        routed: dict[str, Any],
        error: Exception,
    ) -> dict[str, Any]:
        return {
            **routed,
            "status": "error",
            "answer": CHATBOT_TECHNICAL_ERROR_MESSAGE,
            "source": "orchestrator",
            "error_type": type(error).__name__,
        }