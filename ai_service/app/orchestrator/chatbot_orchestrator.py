import re
from datetime import date
from typing import Any

from app.core.llm_response_cleaner import strip_leading_greeting, strip_llm_sources_section
from app.core.chatbot_messages import (
    CHATBOT_GENERIC_RECOMMENDATION_CLARIFICATION_MESSAGE,
    CHATBOT_GENERIC_RECOMMENDATION_CLARIFICATION_MESSAGE_EN,
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
    CHATBOT_PROMOTION_CONTEXT_CLARIFICATION_MESSAGE,
    CHATBOT_PROMOTION_CONTEXT_CLARIFICATION_MESSAGE_EN,
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
from app.tools.kpi_data_tool import KPIDataTool
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
    "can you stop",
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
    # French "peux-tu" action requests
    "peux-tu modifier",
    "peux-tu appliquer",
    "peux-tu approuver",
    "peux-tu rejeter",
    "peux-tu arrêter cette",
    "peux-tu créer",
    "peux-tu changer",
    "peux-tu supprimer",
    "peux-tu mettre à jour",
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
    "clarify_promotion_context": CHATBOT_PROMOTION_CONTEXT_CLARIFICATION_MESSAGE_EN,
    "clarify_store": CHATBOT_STORE_CLARIFICATION_MESSAGE,
    "clarify_product": CHATBOT_PRODUCT_CLARIFICATION_MESSAGE_EN,
    "clarify_price_requests": CHATBOT_PRICE_REQUEST_CLARIFICATION_MESSAGE_EN,
    "generic_recommendation_clarification": CHATBOT_GENERIC_RECOMMENDATION_CLARIFICATION_MESSAGE_EN,
    "ambiguous_question": None,
}

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

# Kept as empty fallback list; add phrases here for any future generic ambiguity.
_AMBIGUOUS_PHRASES: list[str] = []

# T205 — Price-review detection: questions asking which price to revisit first.
# Used both for intent routing (already in step 3b) and for post-fetch filtering.
_PRICE_REVIEW_PHRASES: tuple[str, ...] = (
    "prix devrais je revoir",
    "prix devrais-je revoir",
    "prix dois je revoir",
    "prix dois-je revoir",
    "prix a revoir",
    "prix à revoir",
    "prix revoir en priorite",
    "prix revoir en priorité",
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

# Anomaly types that directly relate to pricing (as opposed to promotional anomalies).
_PRICE_REVIEW_ANOMALY_TYPES: frozenset[str] = frozenset(
    {"PRICE_ABOVE_REFERENCE", "INTER_STORE_PRICE_GAP"}
)

# T210 — Business priority order for "anomalies critiques" questions.
_CRITICAL_ANOMALY_PRIORITY: list[str] = [
    "PRICE_ABOVE_REFERENCE",
    "INEFFECTIVE_DISCOUNT",
    "UNDERPERFORMING_PROMO",
    "INTER_STORE_PRICE_GAP",
]

_CRITICAL_ANOMALY_PHRASES: tuple[str, ...] = (
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

# Anomaly types related to promotional margin impact.
_PROMO_MARGIN_ANOMALY_TYPES: frozenset[str] = frozenset(
    {"INEFFECTIVE_DISCOUNT", "UNDERPERFORMING_PROMO"}
)

# T-A6 — Decision KPI guidance phrases: questions asking which indicators to check
# before a pricing decision.  The block must be placed before step 5 (explain_kpi)
# so that bare "kpi" in the question does not route to the KPI definition service.
_DECISION_KPI_PHRASES: tuple[str, ...] = (
    # FR accentuated — quel/quels indicateur(s) … avant (de) décider
    "quel indicateur regarder avant décision",
    "quels indicateurs regarder avant décision",
    "quel indicateur regarder avant de décider",
    "quels indicateurs regarder avant de décider",
    "quels indicateurs dois-je regarder avant de prendre une décision",
    "quels indicateurs dois je regarder avant de prendre une décision",
    # FR non-accentuated equivalents
    "quel indicateur regarder avant decision",
    "quels indicateurs regarder avant decision",
    "quel indicateur regarder avant de decider",
    "quels indicateurs regarder avant de decider",
    "quels indicateurs dois-je regarder avant de prendre une decision",
    "quels indicateurs dois je regarder avant de prendre une decision",
    # FR accentuated — quel/quels KPI … avant (de) décider
    "quel kpi regarder avant décision",
    "quels kpi regarder avant décision",
    "quels kpi regarder avant de décider",
    "kpi avant décision",
    "kpi avant de décider",
    "quels kpi sont importants pour décider",
    # FR non-accentuated equivalents
    "quel kpi regarder avant decision",
    "quels kpi regarder avant decision",
    "quels kpi regarder avant de decider",
    "kpi avant decision",
    "kpi avant de decider",
    "quels kpi sont importants pour decider",
    # Short forms — indicateur(s) + avant
    "indicateur avant décision",
    "indicateurs avant décision",
    "indicateurs avant de décider",
    "indicateur avant changement de prix",
    "indicateur avant promotion",
    "indicateur avant decision",
    "indicateurs avant decision",
    "indicateurs avant de decider",
    # Broader decisional support phrases
    "sur quoi me baser avant de changer un prix",
    "que vérifier avant une décision pricing",
    "que verifier avant une decision pricing",
    "quels éléments vérifier avant une décision pricing",
    "quels elements verifier avant une decision pricing",
    "aide à la décision pricing",
)

# Phrases indicating the user wants to know which promotion to analyse/prioritise.
_PROMO_ANALYSIS_PHRASES: tuple[str, ...] = (
    "quelle promotion dois-je analyser",
    "quelle promotion dois je analyser",
    "promotion à analyser",
    "promotion a analyser",
    "promotion prioritaire",
    "quelle promo regarder",
    "quelle promo analyser",
    "quelle promo dois-je",
    "quelle promo dois je",
)

# Phrases indicating the user asks about bad margin impact from a promotion.
_MARGIN_IMPACT_PHRASES: tuple[str, ...] = (
    "mauvais impact marge",
    "impact marge négatif",
    "impact marge negatif",
    "promotion dégrade la marge",
    "promotion degrade la marge",
    "dégrade la marge",
    "degrade la marge",
    "bad margin impact",
    "promotion margin issue",
    "impact négatif sur la marge",
    "impact negatif sur la marge",
    "promotion a un mauvais impact",
    "promotion qui dégrade",
    "promotion qui degrade",
)

# Business severity level per anomaly type (deduced, not stored as a DB field).
_ANOMALY_SEVERITY: dict[str, str] = {
    "PRICE_ABOVE_REFERENCE": "CRITICAL",
    "INEFFECTIVE_DISCOUNT": "HIGH",
    "UNDERPERFORMING_PROMO": "MEDIUM",
    "INTER_STORE_PRICE_GAP": "MEDIUM",
}

# Phrases for ambiguous promotion questions requiring a specific promotion ID.
_CLARIFY_PROMOTION_CONTEXT_PHRASES: list[str] = [
    "cette promotion",
    "cette promo",
    "pourquoi cette promo",
    "pourquoi cette promotion",
    "this promotion",
    "dois-je arrêter",
    "dois je arreter",
    "dois-je prolonger cette",
    "dois-je stopper cette",
    "dois je stopper cette",
]

# T210 — Static bilingual definitions for each anomaly type.
# Used by explain_anomaly_definition intent so no data call is needed.
_ANOMALY_DEFINITION_TEXTS: dict[str, dict] = {
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


class ChatbotOrchestrator:
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
        self.business_rules_service = (
            business_rules_service or BusinessRulesExplanationService()
        )
        self.rbac_service = rbac_service or RBACExplanationService()
        self.anomaly_tool = anomaly_tool or AnomalyTool()
        self.kpi_service = kpi_service or KPIExplanationService()
        self.kpi_data_tool = kpi_data_tool or KPIDataTool()
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

        if intent == "chatbot_capabilities":
            return {
                **routed,
                "status": "answered",
                "answer": self._build_chatbot_capabilities_response(lang=lang),
                "source": "orchestrator",
            }

        if intent == "chatbot_limits":
            return {
                **routed,
                "status": "answered",
                "answer": self._build_chatbot_limits_response(lang=lang),
                "source": "orchestrator",
            }

        if intent == "decision_kpi_guidance":
            return {
                **routed,
                "status": "answered",
                "answer": self._build_decision_kpi_response(lang=lang),
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

        if intent == "explain_anomaly_definition":
            try:
                answer = self._answer_anomaly_definition_question(question, lang)
                return {
                    **routed,
                    "status": "answered",
                    "answer": answer,
                    "source": "anomaly_tool",
                }
            except Exception as error:
                return self._build_error_response(routed, error)

        if intent == "list_anomalies":
            if not user_email:
                return {
                    **routed,
                    "status": "missing_context",
                    "answer": CHATBOT_MISSING_USER_EMAIL_MESSAGE,
                    "source": "orchestrator",
                }
            try:
                answer = self._answer_general_anomalies_question(question, user_email, lang)
                return {
                    **routed,
                    "status": "answered",
                    "answer": answer,
                    "source": "anomaly_tool",
                }
            except Exception as error:
                return self._build_error_response(routed, error)

        if intent == "get_kpi_data":
            try:
                answer = self._answer_kpi_data_question(question, user_email, lang)
                return {
                    **routed,
                    "status": "answered",
                    "answer": answer,
                    "source": "kpi_data_tool",
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
                answer = self._answer_price_change_requests_question(question, user_email, lang)
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
                answer = self._answer_promotions_question(question, user_email, lang)
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
                answer = self._answer_prices_question(question, user_email, lang)
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
                answer = self._answer_reference_data_question(question, user_email, lang)
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
                rag_response = self._answer_documentary_question(question, lang=lang)
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
                "qui peut approuver",
                "qui peut rejeter",
                "qui peut refuser",
                "qui peut créer",
                "refuser une demande",
                "rejeter une demande",
                "autorisé à",
                "autorise a changer",
                # French RBAC phrases — scope visibility
                "pourquoi je ne peux pas voir",
                "pourquoi je ne vois pas",
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
                # Explanatory price rule questions — must be checked before price mismatch (3a)
                # so "prix magasin" and "prix pays" in that section don't intercept them.
                "pourquoi un prix magasin peut",
                "pourquoi un prix magasin est different",
                "pourquoi un prix est different du prix pays",
                "pourquoi le prix magasin differe",
                "regle prix magasin",
                "pourquoi un prix magasin",
            ],
        ):
            return "explain_business_rule"

        # 2.5: Documentary anomaly handling questions — placed before step 3b
        # so "anomalie" in the question does not route to list_anomalies.
        if self._contains_any_phrase(
            normalized_question,
            [
                "que faire avec une anomalie prix",
                "que dois-je faire avec une anomalie prix",
                "que dois je faire avec une anomalie prix",
            ],
        ):
            return "documentary_knowledge"

        # 3.pre1: Anomaly type definition — static response, no data call needed.
        # Must come before step 3a so "price_above_reference" in the question
        # does not trigger the store-scoped mismatch route.
        if self._contains_any_phrase(
            normalized_question,
            [
                "explique price_above_reference",
                "explain price_above_reference",
                "explique underperforming_promo",
                "explain underperforming_promo",
                "explique ineffective_discount",
                "explain ineffective_discount",
                "explique inter_store_price_gap",
                "explain inter_store_price_gap",
            ],
        ):
            return "explain_anomaly_definition"

        # 3.pre2: General price-type anomaly queries (no store_id required).
        # Placed before step 3a so accented/unaccented "écart de prix" questions
        # do not hit the store-scoped mismatch route that requires store_id.
        if self._contains_any_phrase(
            normalized_question,
            [
                # PRICE_ABOVE_REFERENCE — unaccented (user may omit accents)
                "produits sont au dessus du prix conseille",
                "produits au dessus du prix conseille",
                "prix au dessus du prix conseille",
                "prix conseille",
                "au-dessus du prix conseille",
                # PRICE_ABOVE_REFERENCE — accented (standard French)
                "produits sont au dessus du prix conseillé",
                "produits au dessus du prix conseillé",
                "prix au dessus du prix conseillé",
                "prix conseillé",
                "au-dessus du prix conseillé",
                # PRICE_ABOVE_REFERENCE — English
                "price above reference",
                # INTER_STORE_PRICE_GAP — unaccented
                "magasins ont un ecart de prix",
                "ecart de prix entre magasins",
                "ecart de prix",
                # INTER_STORE_PRICE_GAP — accented
                "magasins ont un écart de prix",
                "écart de prix entre magasins",
                "écart de prix",
                # INTER_STORE_PRICE_GAP — English
                "inter store price gap",
            ],
        ):
            return "list_anomalies"

        # 3a. Price mismatch — specific store-vs-country price queries.
        # Kept separate from general anomalies because this route requires store_id.
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
                "price_above_reference",
            ],
        ):
            return "list_store_country_price_mismatches"

        # 3b. General anomaly listing — all anomaly types without requiring store_id.
        # Also covers margin-impact promotion questions (before explain_kpi which matches "marge").
        if self._contains_any_phrase(
            normalized_question,
            [
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
                # Prioritisation requests — best answered with anomaly data
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
                # Margin impact promotion phrases — must be before explain_kpi (step 5) which matches "marge"
                *_MARGIN_IMPACT_PHRASES,
                # Promotion analysis / prioritisation phrases
                *_PROMO_ANALYSIS_PHRASES,
            ],
        ):
            return "list_anomalies"

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
                "demandes pending",
                "demandes en attente",
                "demandes approved",
                "demandes approuvees",
                "demandes approuvées",
                "demandes validees",
                "demandes validées",
                "demandes rejected",
                "demandes rejetees",
                "demandes rejetées",
                "demandes refusees",
                "demandes refusées",
                "approved requests",
                "rejected requests",
            ],
        ):
            return "list_store_price_changes"

        # 4.5. KPI data — live figures from the backend.
        # Placed before explain_kpi so interrogative data questions route to the tool,
        # not to the static explanation service.
        if self._contains_kpi_data_intent(normalized_question):
            return "get_kpi_data"

        # 4.6. Decision KPI guidance — static list of indicators to check before a pricing decision.
        # Must come before step 5 (explain_kpi) because "kpi" in the question would otherwise
        # trigger the KPI definition service instead of the decisional indicator list.
        if self._contains_any_phrase(normalized_question, list(_DECISION_KPI_PHRASES)):
            return "decision_kpi_guidance"

        # 5. KPI explanation — definitions, formulas, and business interpretation.
        # Note: "explique le chiffre", "explique la marge", etc. are listed here rather than
        # in documentary_knowledge (step 9) so that apostrophe variants in user input
        # ("chiffre d'affaires" with typographic apostrophe) are caught by the substring
        # "explique le chiffre" before reaching the RAG path.
        if self._contains_any_phrase(
            normalized_question,
            [
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
                "comment est calculé",
                "comment interpréter",
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
            ],
        ):
            return "explain_kpi"

        # 6. Promotions — active or scoped promotions from the backend.
        # Bare "show/list promotions" are handled later as clarify_promotions.
        # "produits en promo" is checked here explicitly so it cannot fall through
        # to the reference_data intent at step 8 (which matches "liste les produits").
        if self._contains_any_phrase(
            normalized_question,
            [
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
                "quelle promotion génère",
                "quelle promotion a le plus",
                "promotion a un mauvais",
            ],
        ):
            return "promotions"

        # 7. Prices — price data from the backend.
        # Bare "show/list/what prices" are handled later as clarify_prices.
        # "quel est le prix de" covers both product names and SKUs.
        if self._contains_any_phrase(
            normalized_question,
            [
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
            ],
        ):
            return "prices"

        # 8. Reference data — applicative master data (countries, stores, products,
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
                "liste les pays",
                "quels pays",
                "pays disponibles",
                "pays existants",
                # Stores
                "list stores",
                "what stores",
                "available stores",
                "show stores",
                "liste des magasins",
                "liste les magasins",
                "affiche les magasins",
                "montre les magasins",
                "quels magasins",
                "magasins disponibles",
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
                "quels produits existent",
                "quels magasins existent",
            ],
        ):
            return "reference_data"

        # 8.4. Chatbot capabilities — static response, no RAG needed.
        # Placed before documentary_knowledge so capability questions never fall through to RAG.
        if self._contains_any_phrase(
            normalized_question,
            [
                "que peux-tu expliquer",
                "que peux tu expliquer",
                "que peux-tu faire",
                "que peux tu faire",
                "what can you do",
                "what can you explain",
                "what can the chatbot",
                "que peut expliquer ce chatbot",
                "que peut faire ce chatbot",
                "que peut faire le chatbot",
                "fonctionnalites du chatbot",
                "capacites du chatbot",
                "capacités du chatbot",
                "a quoi sert ce chatbot",
            ],
        ):
            return "chatbot_capabilities"

        # 8.5. Chatbot limits — static response, no RAG needed.
        # Placed before documentary_knowledge so limit questions never fall through to RAG.
        if self._contains_any_phrase(
            normalized_question,
            [
                "quelles sont tes limites",
                "quelles sont les limites du chatbot",
                "quelles sont les limites",
                "limites du chatbot",
                "tes limitations",
                "limitations du chatbot",
                "que ne peux tu pas faire",
                "que ne peux-tu pas faire",
                "what are your limits",
                "what can you not do",
                "what cannot you do",
                "what are your limitations",
            ],
        ):
            return "chatbot_limits"

        # 8.6. Promotion context clarification — "cette promotion" is ambiguous without an ID.
        # Placed before documentary_knowledge so generic promotion phrasing triggers clarification.
        if self._contains_any_phrase(normalized_question, _CLARIFY_PROMOTION_CONTEXT_PHRASES):
            return "clarify_promotion_context"

        # 8.7. Generic recommendation clarification — too vague without a specific topic.
        # Placed before documentary_knowledge so "recommandes-tu" does not fall through to RAG.
        # Note: "comment savoir quoi faire" belongs here, not in decision_kpi_guidance,
        # because it carries no pricing context and requires a clarification question.
        if self._contains_any_phrase(
            normalized_question,
            [
                "quelle action recommandes-tu",
                "quelle action recommandes tu",
                "que recommandes-tu",
                "que recommandes tu",
                "quelle est ta recommandation",
                "quelle est votre recommandation",
                "what do you recommend",
                "what is your recommendation",
                "comment savoir quoi faire",
                "que dois-je faire",
                "que dois je faire",
            ],
        ):
            return "generic_recommendation_clarification"

        # 9. Documentary knowledge — RAG over project documentation.
        # Deliberately placed after operational intents so Tool Calling stays
        # prioritaire for data questions.
        if self._contains_any_phrase(
            normalized_question,
            [
                # Architecture and monitoring
                "monitoring",
                "observability",
                "runbook",
                "incident",
                "architecture",
                "exploitation",
                "documentation",
                "documented",
                "how is monitoring",
                "how is the system",
                "how does the system",
                # Chatbot capabilities — English
                # Note: "what can you do/explain", "what are your limits" are intercepted
                # by steps 8.4/8.5 before reaching here.
                "chatbot capabilities",
                "chatbot limitations",
                "what can the chatbot",
                "how is the chatbot",
                "how does the chatbot work",
                # Chatbot capabilities — French
                # Note: direct "que peux-tu …" / "quelles sont tes limites" variants are
                # intercepted by steps 8.4/8.5 before reaching here.
                "qu'est-ce que le chatbot peut faire",
                "que peux faire ce chatbot",
                # Pricing workflow explanation
                "how does the price change workflow",
                "price change workflow",
                "explain price scope",
                "price scope rule",
                "how are promotions documented",
                "promotion documented",
                "comment fonctionne le workflow",
                "explique le workflow",
                "workflow de changement de prix",
                "processus de changement de prix",
                "workflow pricing",
                "cycle de validation",
                "demande de changement de prix",
                "comment créer une demande",
                "comment soumettre une demande",
                "pourquoi une demande reste",
                # Decision support and analysis guidance
                "que vérifier avant",
                "que dois-je vérifier",
                "comment décider",
                "aide à la décision",
                "comment analyser une promotion",
                "comment savoir si une promotion",
                "comment prioriser",
                "quel indicateur regarder",
                "quel kpi regarder",
                "comment améliorer",
                "que faire avec une anomalie",
                "pourquoi cette promo ne marche pas",
                "comment interpréter un",
                # Promotion explanation and decision support
                "promotion active",
                "explique ce qu est une promotion",
                "qu est ce qu une promotion",
                "comment savoir si une promotion fonctionne",
                "comment savoir si une promotion",
                "ameliorer une promotion",
                # Handling underperforming / ineffective promotions — routes to RAG, not business rules
                "gérer une promotion",
                "gerer une promotion",
                "promotion inefficace",
                "promotion ne marche",
                "promotion echoue",
                "promotion échoue",
                "promotion qui ne fonctionne",
                "que faire si une promotion ne fonctionne",
                "promotion ne fonctionne pas",
                "comment gérer une promotion",
                "comment gerer une promotion",
                # Pricing decision support
                "comment decider si un prix doit etre change",
                "prix doit etre change",
                "que verifier avant de changer un prix",
                "dois je creer une demande de changement",
            ],
        ):
            return "documentary_knowledge"

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
            "get_kpi_data": "kpi_data_tool",
            "list_anomalies": "anomaly_tool",
            "explain_anomaly_definition": "anomaly_tool",
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
            "chatbot_limits": None,
            "chatbot_capabilities": None,
            "decision_kpi_guidance": None,
            "ambiguous_question": None,
            "clarify_prices": None,
            "clarify_promotions": None,
            "clarify_promotion_context": None,
            "clarify_store": None,
            "clarify_product": None,
            "clarify_price_requests": None,
            "generic_recommendation_clarification": None,
        }

        return tool_by_intent.get(intent)

    def _answer_kpi_data_question(
        self, question: str, user_email: str | None, lang: str = "fr"
    ) -> str:
        if not user_email:
            return CHATBOT_MISSING_USER_EMAIL_MESSAGE

        product_id = self.kpi_data_tool.extract_product_id(question)
        store_id = self.kpi_data_tool.extract_store_id(question)
        is_promo = self.kpi_data_tool.extract_is_promo(question)
        date_from, date_to = self.kpi_data_tool.extract_dates(question)
        target_kpi = self.kpi_data_tool.extract_target_kpi(question)

        context = {
            k: v
            for k, v in {
                "product_id": product_id,
                "store_id": store_id,
                "date_from": date_from,
                "date_to": date_to,
            }.items()
            if v is not None
        }

        data = self.kpi_data_tool.get_kpi_summary(
            user_email=user_email,
            product_id=product_id,
            store_id=store_id,
            is_promo=is_promo,
            date_from=date_from,
            date_to=date_to,
        )
        return self.kpi_data_tool.format_response(data, context, target_kpi=target_kpi, lang=lang)

    def _answer_general_anomalies_question(
        self, question: str, user_email: str | None, lang: str = "fr"
    ) -> str:
        if not user_email:
            return CHATBOT_MISSING_USER_EMAIL_MESSAGE

        normalized = question.lower()
        product_match = re.search(r"(?:produit|product)\s+(\d+)", normalized)
        store_match = re.search(r"(?:magasin|store)\s+(\d+)", normalized)
        product_id = int(product_match.group(1)) if product_match else None
        store_id = int(store_match.group(1)) if store_match else None

        anomalies = self.anomaly_tool.list_anomalies(
            user_email=user_email,
            product_id=product_id,
            store_id=store_id,
        )

        is_price_review = self._is_price_review_question(normalized)
        if is_price_review:
            anomalies = [
                a for a in anomalies
                if a.get("anomaly_type") in _PRICE_REVIEW_ANOMALY_TYPES
            ]

        is_margin_impact = self._is_margin_impact_question(normalized)
        if is_margin_impact and not is_price_review:
            anomalies = [
                a for a in anomalies
                if a.get("anomaly_type") in _PROMO_MARGIN_ANOMALY_TYPES
            ]

        is_promo_analysis = self._is_promotion_analysis_question(normalized)
        if is_promo_analysis and not is_price_review and not is_margin_impact:
            anomalies = [
                a for a in anomalies
                if a.get("anomaly_type") in _PROMO_MARGIN_ANOMALY_TYPES
            ]

        # T210 — filter by anomaly type when the question targets a specific type.
        anomaly_type_filter = self._detect_anomaly_type_filter(normalized)
        if anomaly_type_filter and not is_price_review and not is_margin_impact:
            anomalies = [a for a in anomalies if a.get("anomaly_type") == anomaly_type_filter]

        # T210 — sort by business priority when the question asks for critical anomalies.
        is_critical = any(phrase in normalized for phrase in _CRITICAL_ANOMALY_PHRASES)
        if is_critical:
            priority_index = {t: i for i, t in enumerate(_CRITICAL_ANOMALY_PRIORITY)}
            anomalies = sorted(
                anomalies,
                key=lambda a: priority_index.get(a.get("anomaly_type", ""), len(_CRITICAL_ANOMALY_PRIORITY)),
            )

        explained = self.anomaly_tool.explain_anomalies(anomalies)
        return self._format_anomalies_list(
            explained,
            lang=lang,
            is_price_review=is_price_review,
            is_critical=is_critical,
            is_margin_impact=is_margin_impact,
            is_promo_analysis=is_promo_analysis,
            anomaly_type_filter=anomaly_type_filter,
        )

    def _format_anomalies_list(
        self,
        items: list[dict[str, Any]],
        lang: str = "fr",
        is_price_review: bool = False,
        is_critical: bool = False,
        is_margin_impact: bool = False,
        is_promo_analysis: bool = False,
        anomaly_type_filter: str | None = None,
    ) -> str:
        if not items:
            if is_price_review:
                return self._response_service.format_tool_response(
                    summary="Aucune anomalie prix prioritaire n'a été trouvée dans les résultats disponibles.",
                    details=[
                        "Les anomalies promotionnelles existent, mais elles ne répondent pas directement à la question sur les prix.",
                        "Les types attendus pour cette question sont PRICE_ABOVE_REFERENCE ou INTER_STORE_PRICE_GAP.",
                    ],
                    suggested_next_step=(
                        "Consultez les anomalies promotionnelles si vous souhaitez analyser les promotions inefficaces."
                    ),
                    lang=lang,
                )
            if is_margin_impact:
                return self._response_service.format_tool_response(
                    summary="Aucune anomalie de marge promotionnelle détectée dans votre périmètre.",
                    details=[
                        "La criticité de l'impact marge n'est pas disponible comme champ structuré dans les données actuelles.",
                        "Elle est déduite du type d'anomalie : INEFFECTIVE_DISCOUNT (HIGH) et UNDERPERFORMING_PROMO (MEDIUM).",
                    ],
                    suggested_next_step=(
                        "Demandez 'quelle est la performance de la promotion X ?' pour analyser son impact marge via le KPI promotion performance."
                    ),
                    lang=lang,
                )
            if is_promo_analysis:
                return self._response_service.format_tool_response(
                    summary="Aucune anomalie promotionnelle détectée dans votre périmètre.",
                    details=[
                        "Les types attendus sont UNDERPERFORMING_PROMO et INEFFECTIVE_DISCOUNT.",
                        "Si aucune anomalie n'est présente, vos promotions actives sont dans les seuils attendus.",
                    ],
                    suggested_next_step=(
                        "Consultez les KPI de performance promotionnelle pour confirmer l'absence d'anomalie."
                    ),
                    lang=lang,
                )
            if anomaly_type_filter:
                return self._response_service.format_tool_response(
                    summary=f"Aucune anomalie de type {anomaly_type_filter} trouvée pour votre périmètre.",
                    details=["Aucun résultat ne correspond à ce filtre dans les données disponibles."],
                    lang=lang,
                )
            return "Aucune anomalie trouvée pour votre périmètre."

        # T210 — critical view: warn when no price-critical anomalies are present.
        if is_critical:
            price_critical_types = {"PRICE_ABOVE_REFERENCE", "INEFFECTIVE_DISCOUNT"}
            has_price_critical = any(
                item.get("anomaly", item).get("anomaly_type") in price_critical_types
                for item in items
            )
            if not has_price_critical:
                return self._response_service.format_tool_response(
                    summary=f"{len(items)} anomalie(s) détectée(s). Aucune anomalie de sévérité CRITICAL n'est disponible.",
                    details=[
                        "Niveaux de sévérité métier (déduits du type, non stockés en base) :",
                        "  • CRITICAL — PRICE_ABOVE_REFERENCE",
                        "  • HIGH     — INEFFECTIVE_DISCOUNT",
                        "  • MEDIUM   — UNDERPERFORMING_PROMO, INTER_STORE_PRICE_GAP",
                        "Les anomalies actuelles sont de sévérité MEDIUM — traitez-les après les anomalies CRITICAL et HIGH.",
                    ],
                    lang=lang,
                )

        total = len(items)
        displayed = items[: self._MAX_DISPLAYED_RESULTS]
        suffix = (
            f" Affichage des {len(displayed)} premières."
            if total > self._MAX_DISPLAYED_RESULTS
            else ""
        )

        details = []
        for item in displayed:
            anomaly = item.get("anomaly", item)
            expl = item.get("explanation", {})
            anomaly_type = anomaly.get("anomaly_type", "")
            label = expl.get("label", anomaly_type or "Anomalie")
            severity = _ANOMALY_SEVERITY.get(anomaly_type, "")
            severity_str = f" [{severity}]" if severity else ""
            product = anomaly.get("product_id", "?")
            store = anomaly.get("store_id")
            store_str = f" — Magasin {store}" if store else ""
            details.append(f"{label}{severity_str} — Produit {product}{store_str}")

        if is_price_review:
            return self._response_service.format_tool_response(
                summary=f"{total} anomalie(s) prix détectée(s).{suffix}",
                details=details,
                suggested_next_step=(
                    "Comparer le prix magasin avec le prix pays avant de créer une demande de changement de prix."
                ),
                lang=lang,
            )

        if is_promo_analysis:
            return self._response_service.format_tool_response(
                summary=f"{total} anomalie(s) promotionnelle(s) à analyser en priorité.{suffix}",
                details=details,
                suggested_next_step=(
                    "Analysez d'abord les anomalies INEFFECTIVE_DISCOUNT (HIGH), puis UNDERPERFORMING_PROMO (MEDIUM). "
                    "Vérifiez l'uplift revenu, le volume vendu et la marge avant toute décision."
                ),
                lang=lang,
            )

        if is_critical:
            return self._response_service.format_tool_response(
                summary=f"{total} anomalie(s) triée(s) par criticité métier.{suffix}",
                details=details,
                suggested_next_step=(
                    "Traitez en priorité les anomalies PRICE_ABOVE_REFERENCE, puis INEFFECTIVE_DISCOUNT, "
                    "UNDERPERFORMING_PROMO, et enfin INTER_STORE_PRICE_GAP."
                ),
                lang=lang,
            )

        return self._response_service.format_tool_response(
            summary=f"{total} anomalie(s) détectée(s).{suffix}",
            details=details,
            suggested_next_step=(
                "Consultez les détails de chaque anomalie pour prioriser votre plan d'action."
            ),
            lang=lang,
        )

    def _answer_price_change_requests_question(
        self, question: str, user_email: str | None, lang: str = "fr"
    ) -> str:
        normalized = question.lower()
        status: str | None = None
        if self._contains_any_phrase(normalized, ["pending", "waiting", "en attente"]):
            status = "PENDING"
        elif self._contains_any_phrase(
            normalized,
            ["approved", "approuvé", "approuvée", "approuvee", "validé", "validée", "validee"],
        ):
            status = "APPROVED"
        elif self._contains_any_phrase(
            normalized,
            ["rejected", "rejeté", "rejetée", "rejetee", "refusé", "refusée", "refusee"],
        ):
            status = "REJECTED"

        items = self.price_change_request_tool.list_price_change_requests(
            status=status,
            user_email=user_email,
        )
        return self._format_price_change_requests(items, lang=lang)

    def _answer_promotions_question(
        self, question: str, user_email: str | None, lang: str = "fr"
    ) -> str:
        normalized = question.lower()
        active: bool | None = None
        if self._contains_any_phrase(normalized, ["active", "activ"]):
            active = True
        elif "inactive" in normalized:
            active = False

        product_match = re.search(r"(?:produit|product)\s+(\d+)", normalized)
        store_match = re.search(r"(?:magasin|store)\s+(\d+)", normalized)
        product_id = int(product_match.group(1)) if product_match else None
        store_id = int(store_match.group(1)) if store_match else None

        if store_id is None:
            location = self._extract_location_text(normalized)
            if location:
                store = self.reference_data_tool.find_store_by_text(
                    location, user_email=user_email
                )
                if store:
                    store_id = store.get("id")

        items = self.promotion_tool.list_promotions(
            active=active,
            product_id=product_id,
            store_id=store_id,
            user_email=user_email,
        )

        # Business rule: "active" means the promotion period includes today.
        # The backend `active=True` filter only checks the technical status field,
        # so promotions with an expired period may still be returned.
        excluded_expired_count = 0
        if active is True:
            today = date.today()
            in_period: list[dict[str, Any]] = []
            for item in items:
                try:
                    start = date.fromisoformat(str(item.get("start_date", "")))
                    end = date.fromisoformat(str(item.get("end_date", "")))
                    if start <= today <= end:
                        in_period.append(item)
                    else:
                        excluded_expired_count += 1
                except (ValueError, TypeError):
                    in_period.append(item)
            items = in_period

        products_by_id: dict[int, dict[str, Any]] = {}
        if items:
            all_products = self.reference_data_tool.list_products(user_email=user_email)
            products_by_id = {p["id"]: p for p in all_products if "id" in p}

        return self._format_promotions(
            items,
            product_id=product_id,
            store_id=store_id,
            lang=lang,
            products_by_id=products_by_id,
            excluded_expired_count=excluded_expired_count,
        )

    def _answer_prices_question(
        self, question: str, user_email: str | None, lang: str = "fr"
    ) -> str:
        normalized = question.lower()

        # Step 1: numeric IDs from structured syntax ("produit 3", "magasin 2")
        product_match = re.search(r"(?:produit|product)\s+(\d+)", normalized)
        store_match = re.search(r"(?:magasin|store)\s+(\d+)", normalized)
        product_id = int(product_match.group(1)) if product_match else None
        store_id = int(store_match.group(1)) if store_match else None

        # Step 2: SKU lookup — higher priority than name search
        if product_id is None:
            sku = self._extract_sku(question)
            if sku:
                product = self.reference_data_tool.find_product_by_text(sku, user_email=user_email)
                if product:
                    product_id = product.get("id")

        # Step 3: free-text product name search
        if product_id is None:
            product_query = self._extract_product_text_query(question)
            if product_query:
                product = self.reference_data_tool.find_product_by_text(
                    product_query, user_email=user_email
                )
                if product:
                    product_id = product.get("id")

        # Step 4: city / location lookup — uses rfind so "à boucle à Lille"
        # yields "lille" rather than "boucle"
        if store_id is None:
            location = self._extract_location_text(normalized)
            if location:
                store = self.reference_data_tool.find_store_by_text(
                    location, user_email=user_email
                )
                if store:
                    store_id = store.get("id")

        items = self.price_tool.list_prices(
            product_id=product_id,
            store_id=store_id,
            user_email=user_email,
        )
        return self._format_prices(items, product_id=product_id, store_id=store_id, lang=lang)

    _MAX_DISPLAYED_RESULTS = 5

    def _format_price_change_requests(
        self, items: list[dict[str, Any]], lang: str = "fr"
    ) -> str:
        if not items:
            return "Aucune donnée trouvée."
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
            lang=lang,
        )

    def _format_promotions(
        self,
        items: list[dict[str, Any]],
        product_id: int | None = None,
        store_id: int | None = None,
        lang: str = "fr",
        products_by_id: dict[int, dict[str, Any]] | None = None,
        excluded_expired_count: int = 0,
    ) -> str:
        if not items:
            if excluded_expired_count > 0:
                note = (
                    f"{excluded_expired_count} promotion(s) avec statut ACTIVE ont une période expirée "
                    f"et ont été exclues car elles ne sont plus en cours aujourd'hui."
                    if lang == "fr"
                    else f"{excluded_expired_count} ACTIVE promotion(s) had an expired period "
                    f"and were excluded as they are no longer current today."
                )
                return self._response_service.format_tool_response(
                    summary="Aucune promotion réellement en cours aujourd'hui." if lang == "fr" else "No promotion currently in progress today.",
                    details=[note],
                    suggested_next_step=(
                        "Vérifiez dans l'application les promotions expirées si vous souhaitez les prolonger."
                        if lang == "fr"
                        else "Check the application for expired promotions if you wish to extend them."
                    ),
                    lang=lang,
                )
            return "Aucune promotion trouvée." if lang == "fr" else "No promotion found."

        total = len(items)
        displayed = items[: self._MAX_DISPLAYED_RESULTS]
        suffix = (
            f" Affichage des {len(displayed)} premières."
            if total > self._MAX_DISPLAYED_RESULTS
            else ""
        )

        scope_parts = []
        if product_id is not None:
            scope_parts.append(f"produit {product_id}")
        if store_id is not None:
            scope_parts.append(f"magasin {store_id}")
        filters_label = f" (filtre : {', '.join(scope_parts)})" if scope_parts else ""

        today = date.today()
        details = []
        for item in displayed:
            discount_type = item.get("discount_type", "")
            discount_value = item.get("discount_value", "")
            promo_id = item.get("id", "")
            id_label = f"#{promo_id} — " if promo_id else ""
            if discount_type == "PERCENTAGE":
                discount_label = f"{discount_value}%" if lang == "fr" else f"{discount_value}% discount"
            else:
                discount_label = f"prix fixe {discount_value}" if lang == "fr" else f"fixed price {discount_value}"

            store_label = f" — Magasin {item['store_id']}" if item.get("store_id") else ""
            country_label = f" — Pays {item['country_id']}" if (not item.get("store_id") and item.get("country_id")) else ""
            scope_label = store_label or country_label

            pid = item.get("product_id")
            product = (products_by_id or {}).get(pid) if pid is not None else None
            if product:
                product_label = f"{product.get('code', pid)} — {product.get('name', '')}".strip(" —")
            else:
                product_label = f"Produit {pid}"

            # Technical status from the backend
            tech_status = item.get("status", "")
            if tech_status == "ACTIVE":
                status_label = " [actif]" if lang == "fr" else " [active]"
            elif tech_status == "INACTIVE":
                status_label = " [inactif]" if lang == "fr" else " [inactive]"
            else:
                status_label = f" [{tech_status.lower()}]" if tech_status else ""

            # Period status computed from start/end dates vs today
            period_label = ""
            try:
                start = date.fromisoformat(str(item.get("start_date", "")))
                end = date.fromisoformat(str(item.get("end_date", "")))
                if today < start:
                    period_label = " [à venir]" if lang == "fr" else " [upcoming]"
                elif today > end:
                    period_label = " [expirée]" if lang == "fr" else " [expired]"
                else:
                    period_label = " [en cours]" if lang == "fr" else " [current]"
            except (ValueError, TypeError):
                pass

            details.append(
                f"{id_label}{product_label} — {discount_label}"
                f" — {item.get('start_date', '?')} → {item.get('end_date', '?')}"
                f"{scope_label}{status_label}{period_label}"
            )

        excluded_note = (
            f" ({excluded_expired_count} exclue(s) car période expirée.)"
            if excluded_expired_count > 0
            else ""
        )
        return self._response_service.format_tool_response(
            summary=f"{total} promotion(s) en cours aujourd'hui{filters_label}.{suffix}{excluded_note}",
            details=details,
            suggested_next_step="Vérifiez les KPI de chaque promotion avant de les prolonger.",
            lang=lang,
        )

    def _format_prices(
        self,
        items: list[dict[str, Any]],
        product_id: int | None = None,
        store_id: int | None = None,
        lang: str = "fr",
    ) -> str:
        if not items:
            return "Aucun prix trouvé."

        total = len(items)
        displayed = items[: self._MAX_DISPLAYED_RESULTS]
        suffix = (
            f" Affichage des {len(displayed)} premiers."
            if total > self._MAX_DISPLAYED_RESULTS
            else ""
        )

        scope_parts = []
        if product_id is not None:
            scope_parts.append(f"produit {product_id}")
        if store_id is not None:
            scope_parts.append(f"magasin {store_id}")
        filters_label = f" (filtre : {', '.join(scope_parts)})" if scope_parts else ""

        details = []
        for item in displayed:
            code = item.get("product_code", f"Produit {item.get('product_id', '?')}")
            name = item.get("product_name", "")
            amount = item.get("amount", "?")
            currency = item.get("currency_code", "")

            price_type = item.get("price_type", "")
            type_str = f" — {price_type}" if price_type else ""

            price_scope = item.get("price_scope", "")
            item_store_id = item.get("store_id")
            country_id = item.get("country_id")
            if price_scope == "STORE" and item_store_id:
                location_str = f" — Magasin {item_store_id}"
            elif price_scope == "COUNTRY" and country_id:
                location_str = f" — Pays {country_id}"
            elif item_store_id:
                location_str = f" — Magasin {item_store_id}"
            elif country_id:
                location_str = f" — Pays {country_id}"
            else:
                location_str = ""

            effective_from = item.get("effective_from", "")
            effective_to = item.get("effective_to", "")
            period_str = f" — {effective_from} → {effective_to}" if effective_from and effective_to else ""

            status = item.get("status", "")
            if status == "ACTIVE":
                active_str = " [actif]" if lang == "fr" else " [active]"
            elif status == "INACTIVE":
                active_str = " [inactif]" if lang == "fr" else " [inactive]"
            else:
                active_str = f" [{status.lower()}]" if status else ""

            details.append(
                f"{code} — {name} — {amount} {currency}{type_str}{location_str}{period_str}{active_str}".strip(" —")
            )

        if total > 1:
            next_step = (
                "Plusieurs prix existent car il peut y avoir plusieurs scopes (magasin, pays) "
                "ou périodes différentes. Les prix avec statut ACTIVE sont prioritaires."
                if lang == "fr"
                else "Multiple prices exist because there can be several scopes (store, country) "
                "or different periods. Prices with ACTIVE status take priority."
            )
        else:
            next_step = (
                "Comparez avec les prix de référence pays pour identifier d'éventuels écarts."
                if lang == "fr"
                else "Compare with country reference prices to identify potential gaps."
            )

        return self._response_service.format_tool_response(
            summary=f"{total} prix trouvé(s){filters_label}.{suffix}",
            details=details,
            suggested_next_step=next_step,
            lang=lang,
        )

    def _answer_reference_data_question(
        self, question: str, user_email: str | None, lang: str = "fr"
    ) -> str:
        normalized = question.lower()

        if self._contains_any_phrase(normalized, ["countr", "pays"]):
            items = self.reference_data_tool.list_countries(user_email=user_email)
            return self._format_countries(items, lang=lang)

        if self._contains_any_phrase(normalized, ["store", "magasin"]):
            items = self.reference_data_tool.list_stores(user_email=user_email)
            return self._format_stores(items, lang=lang)

        if self._contains_any_phrase(normalized, ["famil", "famille"]):
            items = self.reference_data_tool.list_product_families(user_email=user_email)
            return self._format_product_families(items, lang=lang)

        active: bool | None = None
        if self._contains_any_phrase(normalized, ["active", "actif", "actifs"]):
            active = True

        items = self.reference_data_tool.list_products(active=active, user_email=user_email)
        return self._format_products(items, lang=lang)

    def _format_countries(self, items: list[dict[str, Any]], lang: str = "fr") -> str:
        if not items:
            return "Aucune donnée de référence trouvée."
        return self._response_service.format_tool_response(
            summary=f"{len(items)} pays disponible(s).",
            details=[c["name"] for c in items],
            lang=lang,
        )

    def _format_stores(self, items: list[dict[str, Any]], lang: str = "fr") -> str:
        if not items:
            return "Aucune donnée de référence trouvée."
        return self._response_service.format_tool_response(
            summary=f"{len(items)} magasin(s) disponible(s).",
            details=[s["name"] for s in items],
            lang=lang,
        )

    def _format_product_families(self, items: list[dict[str, Any]], lang: str = "fr") -> str:
        if not items:
            return "Aucune donnée de référence trouvée."
        return self._response_service.format_tool_response(
            summary=f"{len(items)} famille(s) de produits disponible(s).",
            details=[f["name"] for f in items],
            lang=lang,
        )

    def _format_products(self, items: list[dict[str, Any]], lang: str = "fr") -> str:
        if not items:
            return "Aucune donnée de référence trouvée."
        return self._response_service.format_tool_response(
            summary=f"{len(items)} produit(s) trouvé(s).",
            details=[f"{p['code']} — {p['name']}" for p in items],
            lang=lang,
        )

    def _extract_sku(self, question: str) -> str | None:
        match = re.search(r"\b[A-Z]{2}_[0-9]{8,}\b", question, re.IGNORECASE)
        return match.group(0) if match else None

    def _extract_product_text_query(self, question: str) -> str | None:
        normalized = question.lower()
        for prefix in ["quel est le prix de ", "prix de ", "what is the price of ", "price of "]:
            idx = normalized.find(prefix)
            if idx != -1:
                rest = question[idx + len(prefix):]
                return rest.strip() if rest.strip() else None
        return None

    def _extract_location_text(self, normalized: str) -> str | None:
        # rfind picks the LAST preposition so "Ceinture cuir à boucle à Lille"
        # yields "lille" not "boucle"
        last_idx = -1
        last_prefix_len = 0
        for prefix in [" à ", " in ", " at "]:
            idx = normalized.rfind(prefix)
            if idx > last_idx:
                last_idx = idx
                last_prefix_len = len(prefix)
        if last_idx != -1:
            location = normalized[last_idx + last_prefix_len:].strip()
            return location if location else None
        return None

    def _answer_documentary_question(self, question: str, lang: str = "fr") -> dict[str, Any]:
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

        prompt = self._prompt_builder.build(question, relevant_chunks, lang=lang)
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

        if self._contains_any_phrase(normalized_question, _CLARIFY_PROMOTION_CONTEXT_PHRASES):
            return "clarify_promotion_context"

        return None

    def _contains_any_phrase(self, text: str, keywords: list[str]) -> bool:
        return any(keyword in text for keyword in keywords)

    def _is_price_review_question(self, normalized_question: str) -> bool:
        return any(phrase in normalized_question for phrase in _PRICE_REVIEW_PHRASES)

    def _is_margin_impact_question(self, normalized_question: str) -> bool:
        return any(phrase in normalized_question for phrase in _MARGIN_IMPACT_PHRASES)

    def _is_promotion_analysis_question(self, normalized_question: str) -> bool:
        return any(phrase in normalized_question for phrase in _PROMO_ANALYSIS_PHRASES)

    def _contains_kpi_data_intent(self, text: str) -> bool:
        data_phrases = [
            # French — interrogative forms that request a current value
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
            # English — interrogative forms that request a current value
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
            # Revenue synonyms (from former get_country_revenue intent)
            "sales amount",
            "turnover",
        ]
        if self._contains_any_phrase(text, data_phrases):
            return True
        # "\bca\b" — French acronym for chiffre d'affaires; boundary avoids matching "can".
        return bool(re.search(r"\bca\b", text))

    def _answer_anomaly_definition_question(self, question: str, lang: str = "fr") -> str:
        normalized = question.lower()
        # Override language from the trigger keyword when detect_language may have
        # returned "en" for short mixed-language questions like "Explique PRICE_ABOVE_REFERENCE".
        if "explique" in normalized:
            lang = "fr"
        elif "explain" in normalized:
            lang = "en"
        anomaly_type: str | None = None
        for atype in _ANOMALY_DEFINITION_TEXTS:
            if atype.lower() in normalized:
                anomaly_type = atype
                break

        if anomaly_type is None:
            return "Type d'anomalie non reconnu. Les types disponibles sont : PRICE_ABOVE_REFERENCE, UNDERPERFORMING_PROMO, INEFFECTIVE_DISCOUNT, INTER_STORE_PRICE_GAP."

        texts = _ANOMALY_DEFINITION_TEXTS[anomaly_type]
        content = texts.get(lang, texts["en"])
        return self._response_service.format_tool_response(
            summary=content["summary"],
            details=content["details"],
            suggested_next_step=content["next_step"],
            lang=lang,
        )

    def _detect_anomaly_type_filter(self, normalized: str) -> str | None:
        if self._contains_any_phrase(
            normalized,
            [
                # unaccented forms
                "au dessus du prix conseille",
                "au-dessus du prix conseille",
                "produits au dessus",
                "prix conseille",
                # accented forms
                "au dessus du prix conseillé",
                "au-dessus du prix conseillé",
                "prix conseillé",
                # English
                "price above reference",
            ],
        ):
            return "PRICE_ABOVE_REFERENCE"
        if self._contains_any_phrase(
            normalized,
            [
                # unaccented forms
                "ecart de prix entre magasins",
                "magasins ont un ecart",
                "ecart de prix",
                # accented forms
                "écart de prix entre magasins",
                "magasins ont un écart",
                "écart de prix",
                # English
                "inter store price gap",
            ],
        ):
            return "INTER_STORE_PRICE_GAP"
        return None

    def _build_chatbot_capabilities_response(self, lang: str = "fr") -> str:
        if lang == "fr":
            return self._response_service.format_tool_response(
                summary="Je suis l'assistant IA du Pricing Control Tower. Voici ce que je peux expliquer :",
                details=[
                    "Les KPI métier : chiffre d'affaires, marge, volume, panier moyen, performance promo, uplift",
                    "Les anomalies de prix : écarts magasin/pays, promotions inefficaces, remises inefficaces",
                    "Les rôles et permissions RBAC du MVP (Store Manager, Country Director, Pricing Analyst…)",
                    "Les prix actuels par produit et magasin",
                    "Les promotions actives et leurs conditions",
                    "Le workflow de validation des demandes de changement de prix",
                ],
                suggested_next_step=(
                    'Posez une question précise, par exemple : '
                    '"Quelle est la marge du produit 3 ?" ou "Quels sont les rôles RBAC ?"'
                ),
                lang=lang,
            )
        return self._response_service.format_tool_response(
            summary="I am the Pricing Control Tower AI assistant. Here is what I can explain:",
            details=[
                "Business KPIs: revenue, margin, volume, average order value, promo performance, uplift",
                "Price anomalies: store/country price gaps, ineffective promotions and discounts",
                "MVP RBAC roles and permissions (Store Manager, Country Director, Pricing Analyst…)",
                "Current prices by product and store",
                "Active promotions and their conditions",
                "Price change request validation workflow",
            ],
            suggested_next_step=(
                'Ask a specific question, for example: '
                '"What is the margin for product 3?" or "What are the RBAC roles?"'
            ),
            lang=lang,
        )

    def _build_chatbot_limits_response(self, lang: str = "fr") -> str:
        if lang == "fr":
            return self._response_service.format_tool_response(
                summary="Je suis un assistant lecture seule. Voici ce que je ne peux pas faire :",
                details=[
                    "Modifier, créer ou supprimer un prix",
                    "Approuver ou rejeter une demande de changement de prix",
                    "Créer, modifier ou désactiver une promotion",
                    "Écrire en base de données",
                    "Contourner le RBAC — je vois uniquement ce que votre rôle autorise",
                    "Répondre à des questions sur des données sans contexte (magasin, produit ou période)",
                ],
                suggested_next_step=(
                    "Pour toute action (approbation, rejet, changement de prix), "
                    "utilisez le workflow manuel dans l'application."
                ),
                lang=lang,
            )
        return self._response_service.format_tool_response(
            summary="I am a read-only assistant. Here is what I cannot do:",
            details=[
                "Modify, create, or delete a price",
                "Approve or reject a price change request",
                "Create, modify, or deactivate a promotion",
                "Write to the database",
                "Bypass RBAC — I only see what your role allows",
                "Answer data questions without context (store, product, or period)",
            ],
            suggested_next_step=(
                "For any action (approval, rejection, price change), "
                "use the manual workflow in the application."
            ),
            lang=lang,
        )

    def _build_decision_kpi_response(self, lang: str = "fr") -> str:
        if lang == "fr":
            return self._response_service.format_tool_response(
                summary="Avant toute décision pricing, consultez ces indicateurs dans l'ordre :",
                details=[
                    "Chiffre d'affaires — le CA est-il en hausse ou en baisse sur la période ?",
                    "Marge — la marge reste-t-elle au-dessus du seuil acceptable ?",
                    "Volume vendu — les ventes ont-elles évolué avec le prix ou la promotion ?",
                    "Panier moyen (AOV) — l'achat moyen a-t-il changé ?",
                    "Uplift promotionnel — la promotion a-t-elle généré un revenu supplémentaire ?",
                    "Part du CA en promotion — quelle proportion des ventes est sous promotion ?",
                    "Écart prix magasin / prix pays — y a-t-il une anomalie PRICE_ABOVE_REFERENCE ou INTER_STORE_PRICE_GAP ?",
                    "Anomalies détectées — quelles anomalies sont actives (type, sévérité) ?",
                    "Historique des changements de prix — une demande est-elle déjà en cours ?",
                ],
                suggested_next_step=(
                    "Posez une question précise : "
                    "'Quelle est la marge du produit X ?', "
                    "'Quelles anomalies sont détectées ?', "
                    "ou 'Quelle est la performance de la promotion Y ?'."
                ),
                lang=lang,
            )
        return self._response_service.format_tool_response(
            summary="Before any pricing decision, check these indicators in order:",
            details=[
                "Revenue — is revenue trending up or down over the period?",
                "Margin — is margin still above the business floor?",
                "Volume sold — did sales change with the price or promotion?",
                "Average order value (AOV) — has the average purchase changed?",
                "Promotional uplift — did the promotion generate incremental revenue?",
                "Promo sales share — what proportion of sales occurred under a promotion?",
                "Store / country price gap — is there a PRICE_ABOVE_REFERENCE or INTER_STORE_PRICE_GAP anomaly?",
                "Detected anomalies — which anomalies are active (type, severity)?",
                "Price change history — is a request already pending for this product?",
            ],
            suggested_next_step=(
                "Ask a specific question: "
                "'What is the margin for product X?', "
                "'Which anomalies are detected?', "
                "or 'What is the performance of promotion Y?'."
            ),
            lang=lang,
        )

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
