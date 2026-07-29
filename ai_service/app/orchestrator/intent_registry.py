"""Declarative registry of all intent routing rules.

Each IntentRule defines: intent, route_type, priority, phrases (and/or
exact_phrases / regex_patterns), and an optional description.

Rules are ordered by ascending priority (0 = highest precedence).  The
IntentRouter iterates this list and returns the first match, so the ordering
here is the canonical routing priority for the entire chatbot.

All phrase strings are pre-normalized at module load time so that runtime
matching is a simple substring comparison against the already-normalized
question (ChatContext.normalized_question).
"""

from app.intents.anomaly_phrases import (
    ANOMALY_DEFINITION_PHRASES,
    GENERAL_ANOMALY_PHRASES,
    PRICE_MISMATCH_PHRASES,
    PRICE_TYPE_ANOMALY_PHRASES,
)
from app.intents.capability_phrases import (
    CHATBOT_CAPABILITIES_PHRASES,
    CHATBOT_LIMITS_PHRASES,
)
from app.intents.decision_phrases import (
    DECISION_KPI_PHRASES,
    GENERIC_RECOMMENDATION_CLARIFICATION_PHRASES,
)
from app.intents.guardrail_phrases import GUARDRAIL_WRITE_ACTION_PHRASES
from app.intents.pricing_phrases import (
    CLARIFY_PRICE_REQUESTS_EXACT,
    CLARIFY_PRICES_EXACT,
    KPI_DATA_PHRASES,
    KPI_DATA_REGEX,
    KPI_EXPLANATION_PHRASES,
    PRICE_CHANGE_REQUEST_PHRASES,
    PRICES_PHRASES,
)
from app.intents.promotion_phrases import (
    CLARIFY_PROMOTION_CONTEXT_PHRASES,
    CLARIFY_PROMOTION_PHRASES,
    CLARIFY_PROMOTIONS_EXACT,
    PROMOTIONS_PHRASES,
)
from app.intents.rbac_phrases import RBAC_PHRASES
from app.intents.reference_data_phrases import (
    CLARIFY_PRODUCT_PHRASES,
    CLARIFY_STORE_PHRASES,
    REFERENCE_DATA_PHRASES,
)
from app.intents.workflow_phrases import (
    BUSINESS_RULE_PHRASES,
    DOCUMENTARY_ANOMALY_PHRASES,
    DOCUMENTARY_KNOWLEDGE_PHRASES,
    DOCUMENTARY_PROMOTION_DIAGNOSIS_PHRASES,
)
from app.orchestrator.intent_types import Intent, IntentRule, RouteType
from app.orchestrator.normalization import normalize


def _n(phrases: list[str] | tuple[str, ...]) -> list[str]:
    return [normalize(p) for p in phrases]


def _ne(phrases: frozenset[str]) -> frozenset[str]:
    return frozenset(normalize(p) for p in phrases)


INTENT_RULES: list[IntentRule] = [
    # -------------------------------------------------------------------------
    # Priority 0 — Guardrail: read-only enforcement
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.GUARDRAIL,
        route_type=RouteType.GUARDRAIL,
        priority=0,
        phrases=_n(GUARDRAIL_WRITE_ACTION_PHRASES),
        description="Forbidden write action requests — chatbot is read-only",
    ),
    # -------------------------------------------------------------------------
    # Priority 10 — RBAC roles and permissions
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.EXPLAIN_RBAC,
        route_type=RouteType.TOOL,
        priority=10,
        phrases=_n(RBAC_PHRASES),
        description="RBAC role/permission questions",
    ),
    # -------------------------------------------------------------------------
    # Priority 20 — Business rules and workflow explanations
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.EXPLAIN_BUSINESS_RULE,
        route_type=RouteType.TOOL,
        priority=20,
        phrases=_n(BUSINESS_RULE_PHRASES),
        description="Business validation rules, audit, traceability",
    ),
    # -------------------------------------------------------------------------
    # Priority 25 — Documentary anomaly questions → RAG (not data tool)
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.DOCUMENTARY_KNOWLEDGE,
        route_type=RouteType.RAG,
        priority=25,
        phrases=_n(DOCUMENTARY_ANOMALY_PHRASES),
        description="Anomaly handling guidance → documentary RAG, not data tool",
    ),
    # -------------------------------------------------------------------------
    # Priority 30 — Anomaly type definitions (static, no data call)
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.EXPLAIN_ANOMALY_DEFINITION,
        route_type=RouteType.TOOL,
        priority=30,
        phrases=_n(ANOMALY_DEFINITION_PHRASES),
        description="Static anomaly type explanations — no backend call needed",
    ),
    # -------------------------------------------------------------------------
    # Priority 35 — General price-type anomaly queries (no store_id required)
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.LIST_ANOMALIES,
        route_type=RouteType.TOOL,
        priority=35,
        phrases=_n(PRICE_TYPE_ANOMALY_PHRASES),
        description="PRICE_ABOVE_REFERENCE / INTER_STORE_PRICE_GAP without store_id",
    ),
    # -------------------------------------------------------------------------
    # Priority 40 — Store-vs-country price mismatch (requires store_id)
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.LIST_STORE_COUNTRY_PRICE_MISMATCHES,
        route_type=RouteType.TOOL,
        priority=40,
        phrases=_n(PRICE_MISMATCH_PHRASES),
        description="Store-scoped price mismatch queries — requires store_id",
    ),
    # -------------------------------------------------------------------------
    # Priority 45 — General anomaly listing (all types)
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.LIST_ANOMALIES,
        route_type=RouteType.TOOL,
        priority=45,
        phrases=_n(GENERAL_ANOMALY_PHRASES),
        description="All anomaly types including margin/promo sub-questions",
    ),
    # -------------------------------------------------------------------------
    # Priority 50 — Price change requests
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.LIST_STORE_PRICE_CHANGES,
        route_type=RouteType.TOOL,
        priority=50,
        phrases=_n(PRICE_CHANGE_REQUEST_PHRASES),
        description="Price change request listing",
    ),
    # -------------------------------------------------------------------------
    # Priority 55 — KPI data (live figures from backend)
    # Must precede explain_kpi (priority 65) so data questions route to the tool.
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.GET_KPI_DATA,
        route_type=RouteType.TOOL,
        priority=55,
        phrases=_n(KPI_DATA_PHRASES),
        regex_patterns=KPI_DATA_REGEX,
        description="Live KPI figures from backend — precedes KPI explanation",
    ),
    # -------------------------------------------------------------------------
    # Priority 60 — Decision KPI guidance (static)
    # Must precede explain_kpi (65) so "kpi" in decisional questions does not
    # route to the KPI definition service.
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.DECISION_KPI_GUIDANCE,
        route_type=RouteType.STATIC,
        priority=60,
        phrases=_n(list(DECISION_KPI_PHRASES)),
        description="Static indicator checklist before a pricing decision",
    ),
    # -------------------------------------------------------------------------
    # Priority 65 — KPI explanation (definitions and formulas)
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.EXPLAIN_KPI,
        route_type=RouteType.TOOL,
        priority=65,
        phrases=_n(KPI_EXPLANATION_PHRASES),
        description="Conceptual KPI definitions and formulas",
    ),
    # -------------------------------------------------------------------------
    # Priority 70 — Active/scoped promotions (data tool)
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.PROMOTIONS,
        route_type=RouteType.TOOL,
        priority=70,
        phrases=_n(PROMOTIONS_PHRASES),
        description="Promotion data from backend",
    ),
    # -------------------------------------------------------------------------
    # Priority 75 — Price data (data tool)
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.PRICES,
        route_type=RouteType.TOOL,
        priority=75,
        phrases=_n(PRICES_PHRASES),
        description="Price data from backend",
    ),
    # -------------------------------------------------------------------------
    # Priority 80 — Reference data (countries, stores, products, families)
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.REFERENCE_DATA,
        route_type=RouteType.TOOL,
        priority=80,
        phrases=_n(REFERENCE_DATA_PHRASES),
        description="Applicative master data",
    ),
    # -------------------------------------------------------------------------
    # Priority 85 — Chatbot capabilities (static — before RAG)
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.CHATBOT_CAPABILITIES,
        route_type=RouteType.STATIC,
        priority=85,
        phrases=_n(CHATBOT_CAPABILITIES_PHRASES),
        description="Static chatbot capability description",
    ),
    # -------------------------------------------------------------------------
    # Priority 90 — Chatbot limits (static — before RAG)
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.CHATBOT_LIMITS,
        route_type=RouteType.STATIC,
        priority=90,
        phrases=_n(CHATBOT_LIMITS_PHRASES),
        description="Static chatbot limitations description",
    ),
    # -------------------------------------------------------------------------
    # Priority 94 — Specific promotion diagnosis questions (before the vague
    # "cette promotion" clarification catch-all at 95, which would otherwise
    # shadow phrasings like "pourquoi cette promo ne marche pas ?")
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.DOCUMENTARY_KNOWLEDGE,
        route_type=RouteType.RAG,
        priority=94,
        phrases=_n(DOCUMENTARY_PROMOTION_DIAGNOSIS_PHRASES),
        description="Specific 'why isn't this promo working' questions → documentary RAG",
    ),
    # -------------------------------------------------------------------------
    # Priority 95 — Promotion context clarification (before RAG)
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.CLARIFY_PROMOTION_CONTEXT,
        route_type=RouteType.CLARIFICATION,
        priority=95,
        phrases=_n(CLARIFY_PROMOTION_CONTEXT_PHRASES),
        description="Vague 'cette promotion' reference — needs clarification",
    ),
    # -------------------------------------------------------------------------
    # Priority 100 — Generic recommendation clarification (before RAG)
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.GENERIC_RECOMMENDATION_CLARIFICATION,
        route_type=RouteType.CLARIFICATION,
        priority=100,
        phrases=_n(GENERIC_RECOMMENDATION_CLARIFICATION_PHRASES),
        description="Vague recommendation request — needs topic clarification",
    ),
    # -------------------------------------------------------------------------
    # Priority 110 — Documentary knowledge (RAG fallback)
    # Deliberately placed after all operational intents.
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.DOCUMENTARY_KNOWLEDGE,
        route_type=RouteType.RAG,
        priority=110,
        phrases=_n(DOCUMENTARY_KNOWLEDGE_PHRASES),
        description="Documentary knowledge via RAG pipeline",
    ),
    # -------------------------------------------------------------------------
    # Priority 120–124 — Granular clarification intents (T203)
    # Placed after all tool-calling intents so clear questions are never caught.
    # -------------------------------------------------------------------------
    IntentRule(
        intent=Intent.CLARIFY_PRICES,
        route_type=RouteType.CLARIFICATION,
        priority=120,
        exact_phrases=_ne(CLARIFY_PRICES_EXACT),
        description="Bare price command — needs topic clarification",
    ),
    IntentRule(
        intent=Intent.CLARIFY_PROMOTIONS,
        route_type=RouteType.CLARIFICATION,
        priority=121,
        exact_phrases=_ne(CLARIFY_PROMOTIONS_EXACT),
        description="Bare promotion command — needs topic clarification",
    ),
    IntentRule(
        intent=Intent.CLARIFY_PRICE_REQUESTS,
        route_type=RouteType.CLARIFICATION,
        priority=122,
        exact_phrases=_ne(CLARIFY_PRICE_REQUESTS_EXACT),
        description="Bare request command — needs status clarification",
    ),
    IntentRule(
        intent=Intent.CLARIFY_STORE,
        route_type=RouteType.CLARIFICATION,
        priority=123,
        phrases=_n(CLARIFY_STORE_PHRASES),
        description="Vague store reference — needs topic clarification",
    ),
    IntentRule(
        intent=Intent.CLARIFY_PRODUCT,
        route_type=RouteType.CLARIFICATION,
        priority=124,
        phrases=_n(CLARIFY_PRODUCT_PHRASES),
        description="Vague product reference — needs topic clarification",
    ),
    IntentRule(
        intent=Intent.CLARIFY_PROMOTIONS,
        route_type=RouteType.CLARIFICATION,
        priority=125,
        phrases=_n(CLARIFY_PROMOTION_PHRASES),
        description="Vague promotion reference — needs topic clarification",
    ),
]
