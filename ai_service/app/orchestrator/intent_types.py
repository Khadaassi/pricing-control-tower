from dataclasses import dataclass, field
from enum import Enum


class Intent(str, Enum):
    """All recognized chatbot intents.

    Values are kept identical to the strings used in the original orchestrator
    so that existing test assertions and API responses remain unchanged.
    """

    # Guardrail — read-only enforcement
    GUARDRAIL = "guardrail_action_request"

    # RBAC roles and permissions
    EXPLAIN_RBAC = "explain_rbac"

    # Business rules and workflow
    EXPLAIN_BUSINESS_RULE = "explain_business_rule"

    # Anomalies
    EXPLAIN_ANOMALY_DEFINITION = "explain_anomaly_definition"
    LIST_ANOMALIES = "list_anomalies"
    LIST_STORE_COUNTRY_PRICE_MISMATCHES = "list_store_country_price_mismatches"

    # KPI
    GET_KPI_DATA = "get_kpi_data"
    EXPLAIN_KPI = "explain_kpi"
    DECISION_KPI_GUIDANCE = "decision_kpi_guidance"

    # Price change requests
    LIST_STORE_PRICE_CHANGES = "list_store_price_changes"

    # Promotions and prices
    PROMOTIONS = "promotions"
    PRICES = "prices"

    # Reference data
    REFERENCE_DATA = "reference_data"

    # Documentary knowledge (RAG)
    DOCUMENTARY_KNOWLEDGE = "documentary_knowledge"

    # Static responses
    CHATBOT_CAPABILITIES = "chatbot_capabilities"
    CHATBOT_LIMITS = "chatbot_limits"

    # Clarifications
    CLARIFY_PRICES = "clarify_prices"
    CLARIFY_PROMOTIONS = "clarify_promotions"
    CLARIFY_PROMOTION_CONTEXT = "clarify_promotion_context"
    CLARIFY_STORE = "clarify_store"
    CLARIFY_PRODUCT = "clarify_product"
    CLARIFY_PRICE_REQUESTS = "clarify_price_requests"
    GENERIC_RECOMMENDATION_CLARIFICATION = "generic_recommendation_clarification"
    AMBIGUOUS_QUESTION = "ambiguous_question"

    # Unsupported fallback
    UNKNOWN = "unknown"


class RouteType(str, Enum):
    """How the dispatcher should handle an IntentMatch."""

    GUARDRAIL = "guardrail"
    STATIC = "static"
    CLARIFICATION = "clarification"
    TOOL = "tool"
    RAG = "rag"
    UNSUPPORTED = "unsupported"


@dataclass
class IntentRule:
    """Declarative routing rule for a single intent.

    phrases       — substring patterns; match if any is found in the normalized question.
    exact_phrases — the normalized question must equal one of these exactly.
    regex_patterns — Python regex patterns applied to the normalized question.
    priority      — lower value = evaluated earlier; guarantees stable ordering.
    """

    intent: Intent
    route_type: RouteType
    priority: int
    phrases: list[str] = field(default_factory=list)
    exact_phrases: frozenset[str] = field(default_factory=frozenset)
    regex_patterns: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class IntentMatch:
    """Result returned by IntentRouter.

    confidence defaults to 1.0 for all deterministic rules (no LLM involved).
    """

    intent: Intent
    route_type: RouteType
    matched_phrase: str | None = None
    reason: str | None = None
    confidence: float = 1.0
