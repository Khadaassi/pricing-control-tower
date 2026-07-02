import re
from typing import Any

from app.core.llm_response_cleaner import strip_leading_greeting, strip_llm_sources_section
from app.core.chatbot_messages import (
    CHATBOT_MISSING_STORE_ID_MESSAGE,
    CHATBOT_MISSING_USER_EMAIL_MESSAGE,
    CHATBOT_NOT_IMPLEMENTED_MESSAGE,
    CHATBOT_PRICE_CLARIFICATION_MESSAGE,
    CHATBOT_PRICE_CLARIFICATION_MESSAGE_FR,
    CHATBOT_PRICE_REQUEST_CLARIFICATION_MESSAGE,
    CHATBOT_PRICE_REQUEST_CLARIFICATION_MESSAGE_EN,
    CHATBOT_PRODUCT_CLARIFICATION_MESSAGE,
    CHATBOT_PRODUCT_CLARIFICATION_MESSAGE_EN,
    CHATBOT_PROMOTION_CLARIFICATION_MESSAGE,
    CHATBOT_PROMOTION_CLARIFICATION_MESSAGE_EN,
    CHATBOT_STORE_CLARIFICATION_MESSAGE,
    CHATBOT_STORE_CLARIFICATION_MESSAGE_FR,
    CHATBOT_TECHNICAL_ERROR_MESSAGE,
    CHATBOT_UNSUPPORTED_USE_CASE_MESSAGE,
)
from app.core.language_detector import detect_language
from app.services.response_generation_service import ResponseGenerationService
from app.core.config import settings
from app.core.logging_config import get_logger, log_event
from app.core.metrics import increment_chat_tool_usage_total
from app.llm.base import BaseLLMProvider
from app.llm.factory import get_llm_provider
from app.rag.prompt_builder import RAGPromptBuilder
from app.rag.retriever import DocumentRetriever
from app.rag.source_formatter import deduplicate_sources, enrich_sources, format_sources_block
from app.services.business_rules_explanation_service import (
    BusinessRulesExplanationService,
)
from app.services.kpi_explanation_service import KPIExplanationService
from app.services.rbac_explanation_service import RBACExplanationService
from app.tools.anomaly_tool import AnomalyTool
from app.tools.price_change_request_tool import PriceChangeRequestTool
from app.tools.price_tool import PriceTool
from app.tools.promotion_tool import PromotionTool
from app.tools.reference_data_tool import ReferenceDataTool

logger = get_logger("ai_service.orchestrator")

_RAG_FALLBACK_ANSWER = (
    "Je n'ai pas trouvé suffisamment d'informations dans la documentation "
    "du projet pour répondre à cette question de manière fiable."
)

# T201 — centralized keyword groups for guardrail and ambiguity detection.
_GUARDRAIL_PHRASES = [
    # English direct commands
    "can you approve",
    "can you reject",
    "can you apply",
    "can you update the price",
    "can you modify",
    "can you create",
    "can you delete",
    "please approve",
    "please reject",
    "please apply",
    "approve request",
    "reject request",
    "approve this",
    "reject this",
    "apply this",
    "apply the change",
    "apply the price",
    # French direct commands
    "approuve cette",
    "approuve la demande",
    "rejette cette",
    "rejette la demande",
    "applique cette",
    "applique le changement",
    "valide cette demande",
    "valide la demande",
]

# T203 — granular clarification intents replace the single ambiguous_question.
# Exact-match sets for bare, scope-less commands.
_CLARIFY_PRICES_EXACT: frozenset[str] = frozenset(
    {"show prices", "list prices", "what prices", "explain price", "prix"}
)
_CLARIFY_PROMOTIONS_EXACT: frozenset[str] = frozenset(
    {"show promotions", "list promotions", "promotions"}
)
_CLARIFY_PRICE_REQUESTS_EXACT: frozenset[str] = frozenset(
    {"show requests", "list requests"}
)

# Substring phrases for questions that include an entity reference ("store 1", "product 42").
_CLARIFY_STORE_PHRASES = [
    "tell me about store",
    "what about store",
    "analyse this store",
    "analyze this store",
]
_CLARIFY_PRODUCT_PHRASES = [
    "tell me about product",
    "what about product",
    "analyse this product",
    "analyze this product",
]
_CLARIFY_PROMOTION_PHRASES = [
    "tell me about promotion",
]

# Per-language clarification message maps.  Language is detected from the
# question at answer time; the right dict is selected before dispatch.
_CLARIFICATION_MESSAGES_EN: dict[str, str | None] = {
    "clarify_prices": CHATBOT_PRICE_CLARIFICATION_MESSAGE,
    "clarify_promotions": CHATBOT_PROMOTION_CLARIFICATION_MESSAGE_EN,
    "clarify_store": CHATBOT_STORE_CLARIFICATION_MESSAGE,
    "clarify_product": CHATBOT_PRODUCT_CLARIFICATION_MESSAGE_EN,
    "clarify_price_requests": CHATBOT_PRICE_REQUEST_CLARIFICATION_MESSAGE_EN,
    "ambiguous_question": None,
}

_CLARIFICATION_MESSAGES_FR: dict[str, str | None] = {
    "clarify_prices": CHATBOT_PRICE_CLARIFICATION_MESSAGE_FR,
    "clarify_promotions": CHATBOT_PROMOTION_CLARIFICATION_MESSAGE,
    "clarify_store": CHATBOT_STORE_CLARIFICATION_MESSAGE_FR,
    "clarify_product": CHATBOT_PRODUCT_CLARIFICATION_MESSAGE,
    "clarify_price_requests": CHATBOT_PRICE_REQUEST_CLARIFICATION_MESSAGE,
    "ambiguous_question": None,
}

# Kept as empty fallback list; add phrases here for any future generic ambiguity.
_AMBIGUOUS_PHRASES: list[str] = []


class ChatbotOrchestrator:
    def __init__(
        self,
        business_rules_service: BusinessRulesExplanationService | None = None,
        rbac_service: RBACExplanationService | None = None,
        anomaly_tool: AnomalyTool | None = None,
        kpi_service: KPIExplanationService | None = None,
        price_change_request_tool: PriceChangeRequestTool | None = None,
        promotion_tool: PromotionTool | None = None,
        price_tool: PriceTool | None = None,
        reference_data_tool: ReferenceDataTool | None = None,
        document_retriever: DocumentRetriever | None = None,
        llm_provider: BaseLLMProvider | None = None,
        response_service: ResponseGenerationService | None = None,
    ) -> None:
        self.business_rules_service = (
            business_rules_service or BusinessRulesExplanationService()
        )
        self.rbac_service = rbac_service or RBACExplanationService()
        self.anomaly_tool = anomaly_tool or AnomalyTool()
        self.kpi_service = kpi_service or KPIExplanationService()
        self.price_change_request_tool = (
            price_change_request_tool or PriceChangeRequestTool()
        )
        self.promotion_tool = promotion_tool or PromotionTool()
        self.price_tool = price_tool or PriceTool()
        self.reference_data_tool = reference_data_tool or ReferenceDataTool()
        self.document_retriever = document_retriever or DocumentRetriever()
        self.llm_provider = llm_provider or get_llm_provider()
        self._prompt_builder = RAGPromptBuilder()
        self._response_service = response_service or ResponseGenerationService()

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
        lang = detect_language(question)
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
                "answer": self._response_service.format_fallback_response(lang=lang),
                "source": "orchestrator",
            }

        intent = routed["intent"]

        if intent == "guardrail_action_request":
            return {
                **routed,
                "status": "guardrail",
                "answer": self._response_service.format_guardrail_response(lang=lang),
                "source": "orchestrator",
            }

        clarification_messages = _CLARIFICATION_MESSAGES_FR if lang == "fr" else _CLARIFICATION_MESSAGES_EN
        if intent in clarification_messages:
            return {
                **routed,
                "status": "clarification",
                "answer": self._response_service.format_clarification_response(
                    clarification_messages[intent], lang=lang
                ),
                "source": "orchestrator",
            }

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

        if intent == "list_store_price_changes":
            try:
                answer = self._answer_price_change_requests_question(question, user_email)
                return {
                    **routed,
                    "status": "answered",
                    "answer": answer,
                    "source": "price_change_request_tool",
                }
            except Exception as error:
                return self._build_error_response(routed, error)

        if intent == "promotions":
            try:
                answer = self._answer_promotions_question(question, user_email)
                return {
                    **routed,
                    "status": "answered",
                    "answer": answer,
                    "source": "promotion_tool",
                }
            except Exception as error:
                return self._build_error_response(routed, error)

        if intent == "prices":
            try:
                answer = self._answer_prices_question(question, user_email)
                return {
                    **routed,
                    "status": "answered",
                    "answer": answer,
                    "source": "price_tool",
                }
            except Exception as error:
                return self._build_error_response(routed, error)

        if intent == "reference_data":
            try:
                answer = self._answer_reference_data_question(question, user_email)
                return {
                    **routed,
                    "status": "answered",
                    "answer": answer,
                    "source": "reference_data_tool",
                }
            except Exception as error:
                return self._build_error_response(routed, error)

        if intent == "documentary_knowledge":
            try:
                rag_response = self._answer_documentary_question(question)
                return {
                    **routed,
                    **rag_response,
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

        # 0. Guardrail: direct action requests — the chatbot is read-only.
        # Placed first so imperative commands are blocked before any tool routing.
        # Meta-questions ("can the chatbot approve") fall through to business_rule
        # because they do not match the specific direct-command phrases below.
        if self._contains_any_phrase(normalized_question, _GUARDRAIL_PHRASES):
            return "guardrail_action_request"

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
                # French RBAC phrases — roles
                "rôles rbac",
                "roles rbac",
                "quels sont les rôles",
                "quels sont les roles",
                "différents rôles",
                "differents roles",
                "liste des rôles",
                "liste des roles",
                # French RBAC phrases — personal rights/permissions
                "mes droits",
                "mes permissions",
                "quels sont mes droits",
                "quelles sont mes permissions",
                "droits sur le pricing workflow",
                "permissions sur le pricing workflow",
                # French RBAC phrases — who can do what
                "qui a droit",
                "droit de changer",
                "droit de modifier",
                "droit de valider",
                "qui peut changer",
                "qui peut modifier",
                "autorisé à",
                "autorise a changer",
            ],
        ):
            return "explain_rbac"

        # 2. Business rules and chatbot limitations.
        # Note: bare "workflow" and bare "rule" removed — too broad and caused
        # documentary questions like "how does the price change workflow work?" to
        # incorrectly match here. More specific phrases are used instead.
        if self._contains_any_phrase(
            normalized_question,
            [
                "business rule",
                "validation workflow",
                "workflow for",
                "workflow de",
                "le workflow pour",
                "workflow de validation",
                "audit",
                "traceability",
                "approve a price change",
                "reject a price change",
                "apply a price change",
                "chatbot approve",
                "chatbot update",
                "chatbot modify",
                "chatbot peut-il approuver",
                "chatbot peut approuver",
                "chatbot peut-il rejeter",
                "chatbot peut-il valider",
                "chatbot peut-il modifier",
                "règle métier",
                "traçabilité",
                # French business rule phrases — ineffective promotions
                "gérer une promotion",
                "ne fonctionne pas",
                "promotion inefficace",
                "promotion ne marche",
                "promotion échoue",
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

        # 6. Promotions — active or scoped promotions from the backend.
        # Bare "show/list promotions" are handled later as clarify_promotions.
        if self._contains_any_phrase(
            normalized_question,
            [
                "active promotions",
                "list active promotions",
                "what promotions",
                "available promotions",
                "current promotions",
                "promotions for store",
                "promotions for product",
                "liste des promotions",
                "promotions actives",
                "quelles promotions",
            ],
        ):
            return "promotions"

        # 7. Prices — price data from the backend.
        # Bare "show/list/what prices" are handled later as clarify_prices.
        if self._contains_any_phrase(
            normalized_question,
            [
                "prices for product",
                "prices for store",
                "liste des prix",
                "quels prix",
                "prix du produit",
                "prix du magasin",
            ],
        ):
            return "prices"

        # 9. Reference data — applicative master data (countries, stores, products,
        # product families). Placed before RAG so data questions never hit the
        # document retriever.
        if self._contains_any_phrase(
            normalized_question,
            [
                # Countries
                "list countries",
                "what countries",
                "available countries",
                "show countries",
                "liste des pays",
                "quels pays",
                # Stores
                "list stores",
                "what stores",
                "available stores",
                "show stores",
                "liste des magasins",
                "quels magasins",
                # Product families
                "product famil",
                "familles de produits",
                "familles produit",
                # Products
                "list products",
                "list active products",
                "show products",
                "available products",
                "what products",
                "liste des produits",
                "liste les produits",
                "produits actifs",
            ],
        ):
            return "reference_data"

        # 7. Documentary knowledge — RAG over project documentation.
        # Deliberately placed after operational intents so Tool Calling stays
        # prioritaire for data questions.
        if self._contains_any_phrase(
            normalized_question,
            [
                "monitoring",
                "observability",
                "runbook",
                "incident",
                "architecture",
                "exploitation",
                "chatbot capabilities",
                "chatbot limitations",
                "what can the chatbot",
                "how is the chatbot",
                "how does the chatbot work",
                "documentation",
                "documented",
                "how is monitoring",
                "how is the system",
                "how does the system",
                "how does the price change workflow",
                "price change workflow",
                "explain price scope",
                "price scope rule",
                "how are promotions documented",
                "promotion documented",
            ],
        ):
            return "documentary_knowledge"

        # 7. Revenue / sales KPI.
        if self._contains_revenue_intent(normalized_question):
            return "get_country_revenue"

        # 10. Granular clarification intents (T203): recognized topic but missing scope.
        # Placed after all tool-calling intents so clear questions are never intercepted.
        clarification_intent = self._detect_clarification_intent(normalized_question)
        if clarification_intent:
            return clarification_intent

        # Generic ambiguous fallback (kept for any future phrase additions).
        if self._contains_any_phrase(normalized_question, _AMBIGUOUS_PHRASES):
            return "ambiguous_question"

        return "unknown"

    def _select_tool(self, intent: str) -> str | None:
        tool_by_intent = {
            "get_country_revenue": "kpi_tool",
            "list_store_price_changes": "price_change_request_tool",
            "list_store_country_price_mismatches": "anomaly_tool",
            "explain_kpi": "kpi_explanation_tool",
            "explain_business_rule": "business_rules_tool",
            "explain_rbac": "rbac_tool",
            "promotions": "promotion_tool",
            "prices": "price_tool",
            "reference_data": "reference_data_tool",
            "documentary_knowledge": "rag_retriever",
            "guardrail_action_request": None,
            "ambiguous_question": None,
            "clarify_prices": None,
            "clarify_promotions": None,
            "clarify_store": None,
            "clarify_product": None,
            "clarify_price_requests": None,
        }

        return tool_by_intent.get(intent)

    def _answer_price_change_requests_question(
        self, question: str, user_email: str | None
    ) -> str:
        normalized = question.lower()
        status: str | None = None
        if self._contains_any_phrase(normalized, ["pending", "waiting", "en attente"]):
            status = "PENDING"
        elif self._contains_any_phrase(normalized, ["approved", "approuvé", "approuvée"]):
            status = "APPROVED"
        elif self._contains_any_phrase(normalized, ["rejected", "rejeté", "rejetée"]):
            status = "REJECTED"

        items = self.price_change_request_tool.list_price_change_requests(
            status=status,
            user_email=user_email,
        )
        return self._format_price_change_requests(items)

    def _answer_promotions_question(
        self, question: str, user_email: str | None
    ) -> str:
        normalized = question.lower()
        active: bool | None = None
        if self._contains_any_phrase(normalized, ["active", "activ"]):
            active = True
        elif "inactive" in normalized:
            active = False

        items = self.promotion_tool.list_promotions(active=active, user_email=user_email)
        return self._format_promotions(items)

    def _answer_prices_question(
        self, question: str, user_email: str | None
    ) -> str:
        items = self.price_tool.list_prices(user_email=user_email)
        return self._format_prices(items)

    def _format_price_change_requests(self, items: list[dict[str, Any]]) -> str:
        if not items:
            return "No matching data was found."
        details = [
            f"Request #{item['id']} — Product {item['product_id']}"
            f" — {item['status'].lower()}"
            f" — requested price: {item['requested_price_amount']}"
            for item in items
        ]
        has_pending = any(item["status"] == "PENDING" for item in items)
        return self._response_service.format_tool_response(
            summary=f"{len(items)} demande(s) de changement de prix trouvée(s).",
            details=details,
            suggested_next_step=(
                "Consultez le workflow de validation pour les demandes en attente."
                if has_pending
                else None
            ),
        )

    def _format_promotions(self, items: list[dict[str, Any]]) -> str:
        if not items:
            return "No matching data was found."
        details = []
        for item in items:
            discount_type = item.get("discount_type", "")
            discount_value = item.get("discount_value", "")
            if discount_type == "PERCENTAGE":
                discount_label = f"{discount_value}% discount"
            else:
                discount_label = f"fixed price {discount_value}"
            details.append(
                f"Product {item['product_id']} — {discount_label}"
                f" — from {item['start_date']} to {item['end_date']}"
            )
        return self._response_service.format_tool_response(
            summary=f"{len(items)} promotion(s) trouvée(s).",
            details=details,
            suggested_next_step="Vérifiez les promotions avant de les prolonger.",
        )

    def _format_prices(self, items: list[dict[str, Any]]) -> str:
        if not items:
            return "No matching data was found."
        details = []
        for item in items:
            code = item.get("product_code", f"Product {item.get('product_id', '?')}")
            name = item.get("product_name", "")
            amount = item.get("amount", "?")
            currency = item.get("currency_code", "")
            details.append(f"{code} — {name} — {amount} {currency}".strip(" —"))
        return self._response_service.format_tool_response(
            summary=f"{len(items)} prix trouvé(s).",
            details=details,
            suggested_next_step=(
                "Comparez avec les prix de référence pays pour identifier d'éventuels écarts."
            ),
        )

    def _answer_reference_data_question(
        self, question: str, user_email: str | None
    ) -> str:
        normalized = question.lower()

        if self._contains_any_phrase(normalized, ["countr", "pays"]):
            items = self.reference_data_tool.list_countries(user_email=user_email)
            return self._format_countries(items)

        if self._contains_any_phrase(normalized, ["store", "magasin"]):
            items = self.reference_data_tool.list_stores(user_email=user_email)
            return self._format_stores(items)

        if self._contains_any_phrase(normalized, ["famil", "famille"]):
            items = self.reference_data_tool.list_product_families(user_email=user_email)
            return self._format_product_families(items)

        active: bool | None = None
        if self._contains_any_phrase(normalized, ["active", "actif", "actifs"]):
            active = True

        items = self.reference_data_tool.list_products(active=active, user_email=user_email)
        return self._format_products(items)

    def _format_countries(self, items: list[dict[str, Any]]) -> str:
        if not items:
            return "No matching reference data was found."
        return self._response_service.format_tool_response(
            summary=f"{len(items)} pays disponible(s).",
            details=[c["name"] for c in items],
        )

    def _format_stores(self, items: list[dict[str, Any]]) -> str:
        if not items:
            return "No matching reference data was found."
        return self._response_service.format_tool_response(
            summary=f"{len(items)} magasin(s) disponible(s).",
            details=[s["name"] for s in items],
        )

    def _format_product_families(self, items: list[dict[str, Any]]) -> str:
        if not items:
            return "No matching reference data was found."
        return self._response_service.format_tool_response(
            summary=f"{len(items)} famille(s) de produits disponible(s).",
            details=[f["name"] for f in items],
        )

    def _format_products(self, items: list[dict[str, Any]]) -> str:
        if not items:
            return "No matching reference data was found."
        return self._response_service.format_tool_response(
            summary=f"{len(items)} produit(s) trouvé(s).",
            details=[f"{p['code']} — {p['name']}" for p in items],
        )

    def _answer_documentary_question(self, question: str) -> dict[str, Any]:
        chunks = self.document_retriever.search(question, top_k=settings.rag_top_k)

        relevant_chunks = [
            c for c in chunks if c.get("score", 0.0) >= settings.rag_min_score
        ]

        log_event(
            logger,
            "rag_search_performed",
            chunks_retrieved=len(chunks),
            chunks_relevant=len(relevant_chunks),
            min_score=settings.rag_min_score,
        )

        if not relevant_chunks:
            return {
                "answer": _RAG_FALLBACK_ANSWER,
                "source": "rag_retriever",
                "status": "answered",
                "llm_used": False,
                "rag_sources": [],
            }

        prompt = self._prompt_builder.build(question, relevant_chunks)
        raw_answer = self.llm_provider.generate_response(prompt)
        llm_answer = strip_llm_sources_section(strip_leading_greeting(raw_answer))

        enriched = enrich_sources(relevant_chunks)
        deduplicated = deduplicate_sources(enriched)
        sources_block = format_sources_block(deduplicated, settings.rag_max_displayed_sources)
        answer = f"{llm_answer}\n\n{sources_block}" if sources_block else llm_answer

        return {
            "answer": answer,
            "source": "rag_retriever",
            "status": "answered",
            "llm_used": True,
            "rag_sources": deduplicated,
        }

    def _detect_clarification_intent(self, normalized_question: str) -> str | None:
        if normalized_question in _CLARIFY_PRICES_EXACT:
            return "clarify_prices"

        if normalized_question in _CLARIFY_PROMOTIONS_EXACT:
            return "clarify_promotions"

        if normalized_question in _CLARIFY_PRICE_REQUESTS_EXACT:
            return "clarify_price_requests"

        if self._contains_any_phrase(normalized_question, _CLARIFY_STORE_PHRASES):
            return "clarify_store"

        if self._contains_any_phrase(normalized_question, _CLARIFY_PRODUCT_PHRASES):
            return "clarify_product"

        if self._contains_any_phrase(normalized_question, _CLARIFY_PROMOTION_PHRASES):
            return "clarify_promotions"

        return None

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
