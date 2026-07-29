"""Frozen non-regression suite for IntentRouter.

Context: a manual audit (84 questions run directly through IntentRouter.route())
found 17 routing discrepancies during the 2026-07-28 review. That audit was a
throwaway script, never committed — so its exact 84 questions cannot be
reproduced here. This file is the parametrized, pytest-native replacement: one
row per priority tier in app/orchestrator/intent_registry.py (so every rule has
at least one traceable "question -> expected intent/route_type" case), plus a
dedicated section for priority-ordering / substring-shadowing regressions —
including the three concrete false positives fixed as part of this same pass
(see CASES_SHADOWING_REGRESSIONS below).

Any change to intent_registry.py that silently changes where one of these
questions routes should fail a test here.
"""

import pytest

from app.orchestrator.intent_router import IntentRouter
from app.orchestrator.intent_types import Intent, RouteType


@pytest.fixture(scope="module")
def router() -> IntentRouter:
    return IntentRouter()


# One row per priority tier, in ascending priority order — mirrors the
# ordering of INTENT_RULES in intent_registry.py.
CASES_ONE_PER_PRIORITY_TIER: list[tuple[str, str, Intent, RouteType]] = [
    (
        "priority_0_guardrail",
        "approuve cette demande de changement de prix",
        Intent.GUARDRAIL,
        RouteType.GUARDRAIL,
    ),
    ("priority_10_rbac", "quels sont mes droits ?", Intent.EXPLAIN_RBAC, RouteType.TOOL),
    (
        "priority_20_business_rule",
        "explique le workflow de validation",
        Intent.EXPLAIN_BUSINESS_RULE,
        RouteType.TOOL,
    ),
    (
        "priority_25_documentary_anomaly_which_exist",
        "Quelles anomalies existent ?",
        Intent.DOCUMENTARY_KNOWLEDGE,
        RouteType.RAG,
    ),
    (
        "priority_25_documentary_anomaly_how_to_prioritize",
        "Comment prioriser les anomalies ?",
        Intent.DOCUMENTARY_KNOWLEDGE,
        RouteType.RAG,
    ),
    (
        "priority_30_anomaly_definition",
        "explique PRICE_ABOVE_REFERENCE",
        Intent.EXPLAIN_ANOMALY_DEFINITION,
        RouteType.TOOL,
    ),
    (
        "priority_35_list_anomalies_price_type",
        "Quels produits sont au-dessus du prix conseille ?",
        Intent.LIST_ANOMALIES,
        RouteType.TOOL,
    ),
    (
        "priority_40_price_mismatch",
        "show me price mismatch for this store",
        Intent.LIST_STORE_COUNTRY_PRICE_MISMATCHES,
        RouteType.TOOL,
    ),
    (
        "priority_45_list_anomalies_general",
        "montre-moi les anomalies",
        Intent.LIST_ANOMALIES,
        RouteType.TOOL,
    ),
    (
        "priority_50_price_change_requests",
        "demandes de changement de prix en attente",
        Intent.LIST_STORE_PRICE_CHANGES,
        RouteType.TOOL,
    ),
    (
        "priority_55_kpi_data",
        "quel est le chiffre d'affaires ?",
        Intent.GET_KPI_DATA,
        RouteType.TOOL,
    ),
    (
        "priority_60_decision_kpi_guidance",
        "quel indicateur regarder avant decision",
        Intent.DECISION_KPI_GUIDANCE,
        RouteType.STATIC,
    ),
    (
        "priority_65_explain_kpi",
        "explique la marge brute",
        Intent.EXPLAIN_KPI,
        RouteType.TOOL,
    ),
    (
        "priority_70_promotions",
        "liste les promotions actives",
        Intent.PROMOTIONS,
        RouteType.TOOL,
    ),
    (
        "priority_75_prices",
        "quel est le prix de ce produit ?",
        Intent.PRICES,
        RouteType.TOOL,
    ),
    (
        "priority_80_reference_data",
        "liste les magasins",
        Intent.REFERENCE_DATA,
        RouteType.TOOL,
    ),
    (
        "priority_85_chatbot_capabilities",
        "que peux-tu faire ?",
        Intent.CHATBOT_CAPABILITIES,
        RouteType.STATIC,
    ),
    (
        "priority_90_chatbot_limits",
        "quelles sont tes limites ?",
        Intent.CHATBOT_LIMITS,
        RouteType.STATIC,
    ),
    (
        "priority_94_documentary_promotion_diagnosis",
        "Pourquoi cette promo ne marche pas ?",
        Intent.DOCUMENTARY_KNOWLEDGE,
        RouteType.RAG,
    ),
    (
        "priority_95_clarify_promotion_context",
        "cette promotion, dois-je la prolonger ?",
        Intent.CLARIFY_PROMOTION_CONTEXT,
        RouteType.CLARIFICATION,
    ),
    (
        "priority_100_generic_recommendation_clarification",
        "que recommandes-tu ?",
        Intent.GENERIC_RECOMMENDATION_CLARIFICATION,
        RouteType.CLARIFICATION,
    ),
    (
        "priority_110_documentary_knowledge",
        "explique l'architecture du systeme",
        Intent.DOCUMENTARY_KNOWLEDGE,
        RouteType.RAG,
    ),
    (
        "priority_120_clarify_prices",
        "prix",
        Intent.CLARIFY_PRICES,
        RouteType.CLARIFICATION,
    ),
    (
        "priority_121_clarify_promotions_exact",
        "promotions",
        Intent.CLARIFY_PROMOTIONS,
        RouteType.CLARIFICATION,
    ),
    (
        "priority_122_clarify_price_requests",
        "show requests",
        Intent.CLARIFY_PRICE_REQUESTS,
        RouteType.CLARIFICATION,
    ),
    (
        "priority_123_clarify_store",
        "tell me about store 3",
        Intent.CLARIFY_STORE,
        RouteType.CLARIFICATION,
    ),
    (
        "priority_124_clarify_product",
        "tell me about product 5",
        Intent.CLARIFY_PRODUCT,
        RouteType.CLARIFICATION,
    ),
    (
        "priority_125_clarify_promotions_phrase",
        "tell me about promotion 7",
        Intent.CLARIFY_PROMOTIONS,
        RouteType.CLARIFICATION,
    ),
    (
        "fallback_unknown",
        "quel temps fait-il demain ?",
        Intent.UNKNOWN,
        RouteType.UNSUPPORTED,
    ),
]

# Substring-shadowing regressions: a lower-priority (broader) rule must not
# steal a question that a higher-priority (more specific) rule should answer.
CASES_SHADOWING_REGRESSIONS: list[tuple[str, str, Intent, RouteType]] = [
    (
        "guardrail_wins_over_rbac",
        "peux-tu approuver cette demande ?",
        Intent.GUARDRAIL,
        RouteType.GUARDRAIL,
    ),
    (
        "business_rule_wins_over_price_mismatch_for_explanatory_question",
        "pourquoi un prix magasin peut etre different du prix pays ?",
        Intent.EXPLAIN_BUSINESS_RULE,
        RouteType.TOOL,
    ),
    (
        "business_rule_wins_over_documentary_for_ineffective_promo",
        "comment gerer une promotion inefficace ?",
        Intent.EXPLAIN_BUSINESS_RULE,
        RouteType.TOOL,
    ),
    (
        "kpi_data_wins_over_kpi_explanation",
        "quel est le chiffre d'affaires du magasin 3 ?",
        Intent.GET_KPI_DATA,
        RouteType.TOOL,
    ),
    (
        "decision_kpi_guidance_wins_over_kpi_explanation",
        "quel kpi regarder avant decision",
        Intent.DECISION_KPI_GUIDANCE,
        RouteType.STATIC,
    ),
    (
        "generic_recommendation_clarification_wins_over_documentary",
        "que recommandes-tu ?",
        Intent.GENERIC_RECOMMENDATION_CLARIFICATION,
        RouteType.CLARIFICATION,
    ),
    (
        "scoped_promotion_query_not_intercepted_by_clarify_promotion_context",
        "promotions du magasin 3",
        Intent.PROMOTIONS,
        RouteType.TOOL,
    ),
    # --- Fixed 2026-07-28: bare "anomalies"/"cette promo" substrings were
    # shadowing more specific, already-existing documentary phrases below
    # them in priority order. See app/intents/workflow_phrases.py.
    (
        "conceptual_which_anomalies_exist_not_swallowed_by_bare_anomalies",
        "Quelles anomalies existent ?",
        Intent.DOCUMENTARY_KNOWLEDGE,
        RouteType.RAG,
    ),
    (
        "how_to_prioritize_anomalies_not_swallowed_by_bare_anomalies",
        "Comment prioriser les anomalies ?",
        Intent.DOCUMENTARY_KNOWLEDGE,
        RouteType.RAG,
    ),
    (
        "why_promo_not_working_not_swallowed_by_vague_clarify_promotion_context",
        "Pourquoi cette promo ne marche pas ?",
        Intent.DOCUMENTARY_KNOWLEDGE,
        RouteType.RAG,
    ),
]


@pytest.mark.parametrize(
    "question, expected_intent, expected_route_type",
    [case[1:] for case in CASES_ONE_PER_PRIORITY_TIER],
    ids=[case[0] for case in CASES_ONE_PER_PRIORITY_TIER],
)
def test_routing_by_priority_tier(
    router: IntentRouter,
    question: str,
    expected_intent: Intent,
    expected_route_type: RouteType,
) -> None:
    match = router.route(question)
    assert match.intent == expected_intent
    assert match.route_type == expected_route_type


@pytest.mark.parametrize(
    "question, expected_intent, expected_route_type",
    [case[1:] for case in CASES_SHADOWING_REGRESSIONS],
    ids=[case[0] for case in CASES_SHADOWING_REGRESSIONS],
)
def test_routing_shadowing_regressions(
    router: IntentRouter,
    question: str,
    expected_intent: Intent,
    expected_route_type: RouteType,
) -> None:
    match = router.route(question)
    assert match.intent == expected_intent
    assert match.route_type == expected_route_type
