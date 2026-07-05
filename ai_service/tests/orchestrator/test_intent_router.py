"""Unit tests for IntentRouter deterministic routing.

Covers each intent in priority order, verifies:
  - Correct Intent value returned
  - Correct RouteType returned
  - Priority ordering (higher-priority rules win over lower-priority ones)
  - Accent-insensitive matching via normalize()
  - Unknown/unsupported questions fall back to UNKNOWN + UNSUPPORTED
"""

import pytest

from app.orchestrator.intent_router import IntentRouter
from app.orchestrator.intent_types import Intent, RouteType


@pytest.fixture(scope="module")
def router() -> IntentRouter:
    return IntentRouter()


# ---------------------------------------------------------------------------
# Guardrail — priority 0
# ---------------------------------------------------------------------------

class TestGuardrailRouting:
    def test_approve_action_blocked(self, router: IntentRouter) -> None:
        m = router.route("approuve cette demande")
        assert m.intent == Intent.GUARDRAIL
        assert m.route_type == RouteType.GUARDRAIL

    def test_reject_action_blocked(self, router: IntentRouter) -> None:
        m = router.route("rejette la demande de prix")
        assert m.intent == Intent.GUARDRAIL

    def test_apply_price_change_blocked(self, router: IntentRouter) -> None:
        m = router.route("applique le changement de prix")
        assert m.intent == Intent.GUARDRAIL

    def test_create_promotion_blocked(self, router: IntentRouter) -> None:
        m = router.route("peux-tu creer une promotion pour ce produit")
        assert m.intent == Intent.GUARDRAIL

    def test_delete_blocked(self, router: IntentRouter) -> None:
        m = router.route("peux-tu supprimer cette entrée")
        assert m.intent == Intent.GUARDRAIL


# ---------------------------------------------------------------------------
# RBAC — priority 10
# ---------------------------------------------------------------------------

class TestRbacRouting:
    def test_french_roles_question(self, router: IntentRouter) -> None:
        m = router.route("quels sont les différents rôles ?")
        assert m.intent == Intent.EXPLAIN_RBAC
        assert m.route_type == RouteType.TOOL

    def test_no_accent_roles_question(self, router: IntentRouter) -> None:
        m = router.route("quels sont les differents roles ?")
        assert m.intent == Intent.EXPLAIN_RBAC

    def test_droits_question(self, router: IntentRouter) -> None:
        m = router.route("Quels sont mes droits ?")
        assert m.intent == Intent.EXPLAIN_RBAC

    def test_permissions_question(self, router: IntentRouter) -> None:
        m = router.route("Explique mes permissions ?")
        assert m.intent == Intent.EXPLAIN_RBAC

    def test_qui_a_le_droit(self, router: IntentRouter) -> None:
        m = router.route("qui a droit de changer un prix ?")
        assert m.intent == Intent.EXPLAIN_RBAC

    def test_pricing_workflow_rights(self, router: IntentRouter) -> None:
        m = router.route("Quels sont mes droits sur le pricing workflow ?")
        assert m.intent == Intent.EXPLAIN_RBAC

    def test_store_manager_role(self, router: IntentRouter) -> None:
        m = router.route("que peut faire un store manager ?")
        assert m.intent == Intent.EXPLAIN_RBAC

    def test_rbac_precedes_guardrail_for_plain_query(self, router: IntentRouter) -> None:
        # "modifier" alone as a role-context question should not be guardrailed
        m = router.route("qui peut modifier un prix ?")
        assert m.intent == Intent.EXPLAIN_RBAC

    def test_pourquoi_pas_voir_magasin(self, router: IntentRouter) -> None:
        m = router.route("Pourquoi je ne peux pas voir ce magasin ?")
        assert m.intent == Intent.EXPLAIN_RBAC


# ---------------------------------------------------------------------------
# Business rules — priority 20
# ---------------------------------------------------------------------------

class TestBusinessRuleRouting:
    def test_validation_workflow(self, router: IntentRouter) -> None:
        m = router.route("explique le workflow de validation")
        assert m.intent == Intent.EXPLAIN_BUSINESS_RULE
        assert m.route_type == RouteType.TOOL

    def test_regle_metier(self, router: IntentRouter) -> None:
        m = router.route("quelle est la règle métier ?")
        assert m.intent == Intent.EXPLAIN_BUSINESS_RULE

    def test_ineffective_promotion_routes_to_business_rule(self, router: IntentRouter) -> None:
        m = router.route("comment gérer une promotion qui ne fonctionne pas ?")
        assert m.intent == Intent.EXPLAIN_BUSINESS_RULE

    def test_promotion_ne_fonctionne_pas(self, router: IntentRouter) -> None:
        m = router.route("La promotion ne fonctionne pas, que faire ?")
        assert m.intent == Intent.EXPLAIN_BUSINESS_RULE

    def test_promotion_inefficace(self, router: IntentRouter) -> None:
        m = router.route("cette promotion inefficace, que faire ?")
        assert m.intent == Intent.EXPLAIN_BUSINESS_RULE

    def test_tracabilite(self, router: IntentRouter) -> None:
        m = router.route("comment assurer la traçabilité ?")
        assert m.intent == Intent.EXPLAIN_BUSINESS_RULE

    def test_audit(self, router: IntentRouter) -> None:
        m = router.route("comment fonctionne l'audit ?")
        assert m.intent == Intent.EXPLAIN_BUSINESS_RULE


# ---------------------------------------------------------------------------
# Anomaly definitions — priority 30
# ---------------------------------------------------------------------------

class TestAnomalyDefinitionRouting:
    def test_explain_price_above_reference(self, router: IntentRouter) -> None:
        m = router.route("explique PRICE_ABOVE_REFERENCE")
        assert m.intent == Intent.EXPLAIN_ANOMALY_DEFINITION
        assert m.route_type == RouteType.TOOL

    def test_explain_underperforming_promo(self, router: IntentRouter) -> None:
        m = router.route("explique UNDERPERFORMING_PROMO")
        assert m.intent == Intent.EXPLAIN_ANOMALY_DEFINITION


# ---------------------------------------------------------------------------
# List anomalies — priorities 35 & 45
# ---------------------------------------------------------------------------

class TestListAnomaliesRouting:
    def test_anomalies_critiques(self, router: IntentRouter) -> None:
        m = router.route("Quelles sont les anomalies critiques ?")
        assert m.intent == Intent.LIST_ANOMALIES
        assert m.route_type == RouteType.TOOL

    def test_anomalies_generales(self, router: IntentRouter) -> None:
        m = router.route("montre-moi les anomalies")
        assert m.intent == Intent.LIST_ANOMALIES

    def test_produits_au_dessus_prix_conseille(self, router: IntentRouter) -> None:
        m = router.route("Quels produits sont au-dessus du prix conseille ?")
        assert m.intent == Intent.LIST_ANOMALIES

    def test_show_priority_anomalies_en(self, router: IntentRouter) -> None:
        m = router.route("Show me the priority anomalies")
        assert m.intent == Intent.LIST_ANOMALIES


# ---------------------------------------------------------------------------
# Store-vs-country price mismatches — priority 40
# ---------------------------------------------------------------------------

class TestPriceMismatchRouting:
    def test_ecart_de_prix(self, router: IntentRouter) -> None:
        m = router.route("show me price mismatch for this store")
        assert m.intent == Intent.LIST_STORE_COUNTRY_PRICE_MISMATCHES
        assert m.route_type == RouteType.TOOL

    def test_mismatch_keyword(self, router: IntentRouter) -> None:
        m = router.route("show price mismatch for my store")
        assert m.intent == Intent.LIST_STORE_COUNTRY_PRICE_MISMATCHES


# ---------------------------------------------------------------------------
# KPI data — priority 55
# ---------------------------------------------------------------------------

class TestKpiDataRouting:
    def test_chiffre_affaires(self, router: IntentRouter) -> None:
        m = router.route("quel est le chiffre d'affaires ?")
        assert m.intent == Intent.GET_KPI_DATA
        assert m.route_type == RouteType.TOOL

    def test_ca_regex(self, router: IntentRouter) -> None:
        m = router.route("montre-moi le CA du magasin")
        assert m.intent == Intent.GET_KPI_DATA

    def test_taux_marge(self, router: IntentRouter) -> None:
        m = router.route("quelle est la marge du magasin ?")
        assert m.intent == Intent.GET_KPI_DATA


# ---------------------------------------------------------------------------
# KPI explanation — priority 65
# ---------------------------------------------------------------------------

class TestExplainKpiRouting:
    def test_explique_marge(self, router: IntentRouter) -> None:
        m = router.route("explique la marge brute")
        assert m.intent == Intent.EXPLAIN_KPI
        assert m.route_type == RouteType.TOOL

    def test_comment_calculer_kpi(self, router: IntentRouter) -> None:
        m = router.route("comment est calculé le KPI ?")
        assert m.intent == Intent.EXPLAIN_KPI


# ---------------------------------------------------------------------------
# Promotions — priority 70
# ---------------------------------------------------------------------------

class TestPromotionsRouting:
    def test_promotions_actives(self, router: IntentRouter) -> None:
        m = router.route("liste les promotions actives")
        assert m.intent == Intent.PROMOTIONS
        assert m.route_type == RouteType.TOOL

    def test_list_active_promotions_en(self, router: IntentRouter) -> None:
        m = router.route("List active promotions")
        assert m.intent == Intent.PROMOTIONS

    def test_promotions_not_intercepted_by_business_rules(self, router: IntentRouter) -> None:
        # Simple promotion listing must not hit business rule phrases
        m = router.route("liste les promotions")
        assert m.intent == Intent.PROMOTIONS


# ---------------------------------------------------------------------------
# Prices — priority 75
# ---------------------------------------------------------------------------

class TestPricesRouting:
    def test_quel_est_le_prix(self, router: IntentRouter) -> None:
        m = router.route("quel est le prix de ce produit ?")
        assert m.intent == Intent.PRICES
        assert m.route_type == RouteType.TOOL

    def test_show_price_en(self, router: IntentRouter) -> None:
        m = router.route("what is the price of product 42")
        assert m.intent == Intent.PRICES


# ---------------------------------------------------------------------------
# Reference data — priority 80
# ---------------------------------------------------------------------------

class TestReferenceDataRouting:
    def test_liste_magasins(self, router: IntentRouter) -> None:
        m = router.route("liste les magasins")
        assert m.intent == Intent.REFERENCE_DATA
        assert m.route_type == RouteType.TOOL

    def test_liste_pays(self, router: IntentRouter) -> None:
        m = router.route("liste les pays")
        assert m.intent == Intent.REFERENCE_DATA

    def test_liste_produits(self, router: IntentRouter) -> None:
        m = router.route("liste les produits")
        assert m.intent == Intent.REFERENCE_DATA


# ---------------------------------------------------------------------------
# Chatbot capabilities / limits — priorities 85 & 90
# ---------------------------------------------------------------------------

class TestChatbotStaticRouting:
    def test_que_peux_tu_faire(self, router: IntentRouter) -> None:
        m = router.route("que peux-tu faire ?")
        assert m.intent == Intent.CHATBOT_CAPABILITIES
        assert m.route_type == RouteType.STATIC

    def test_tes_limites(self, router: IntentRouter) -> None:
        m = router.route("quelles sont tes limites ?")
        assert m.intent == Intent.CHATBOT_LIMITS
        assert m.route_type == RouteType.STATIC


# ---------------------------------------------------------------------------
# Documentary knowledge (RAG) — priority 110
# ---------------------------------------------------------------------------

class TestDocumentaryKnowledgeRouting:
    def test_architecture(self, router: IntentRouter) -> None:
        m = router.route("explique l'architecture du système")
        assert m.intent == Intent.DOCUMENTARY_KNOWLEDGE
        assert m.route_type == RouteType.RAG

    def test_monitoring(self, router: IntentRouter) -> None:
        m = router.route("comment fonctionne le monitoring ?")
        assert m.intent == Intent.DOCUMENTARY_KNOWLEDGE

    def test_workflow_de_changement_de_prix(self, router: IntentRouter) -> None:
        m = router.route("explique le workflow de changement de prix")
        assert m.intent == Intent.DOCUMENTARY_KNOWLEDGE


# ---------------------------------------------------------------------------
# Clarification intents — priorities 120–125
# ---------------------------------------------------------------------------

class TestClarificationRouting:
    def test_bare_prix_triggers_clarification(self, router: IntentRouter) -> None:
        m = router.route("prix")
        assert m.intent == Intent.CLARIFY_PRICES
        assert m.route_type == RouteType.CLARIFICATION

    def test_bare_promotions_triggers_clarification(self, router: IntentRouter) -> None:
        m = router.route("promotions")
        assert m.intent == Intent.CLARIFY_PROMOTIONS
        assert m.route_type == RouteType.CLARIFICATION


# ---------------------------------------------------------------------------
# Unknown / unsupported fallback
# ---------------------------------------------------------------------------

class TestUnknownRouting:
    def test_unknown_question_returns_unknown_intent(self, router: IntentRouter) -> None:
        m = router.route("quel temps fait-il demain ?")
        assert m.intent == Intent.UNKNOWN
        assert m.route_type == RouteType.UNSUPPORTED

    def test_empty_string_returns_unknown(self, router: IntentRouter) -> None:
        m = router.route("")
        assert m.intent == Intent.UNKNOWN
        assert m.route_type == RouteType.UNSUPPORTED


# ---------------------------------------------------------------------------
# Priority ordering — lower priority must not shadow higher priority
# ---------------------------------------------------------------------------

class TestPriorityOrdering:
    def test_guardrail_wins_over_rbac_for_approuver_demande(self, router: IntentRouter) -> None:
        # "approuve cette demande" is a write action → guardrail wins
        m = router.route("approuve cette demande de changement de prix")
        assert m.intent == Intent.GUARDRAIL

    def test_rbac_wins_over_documentary_for_roles(self, router: IntentRouter) -> None:
        # Role questions must not fall through to RAG
        m = router.route("quels sont les rôles disponibles ?")
        assert m.intent == Intent.EXPLAIN_RBAC

    def test_business_rule_wins_over_rag_for_ineffective_promo(
        self, router: IntentRouter
    ) -> None:
        # Ineffective-promotion questions must go to business_rules, not RAG
        m = router.route("comment gérer une promotion inefficace ?")
        assert m.intent == Intent.EXPLAIN_BUSINESS_RULE

    def test_kpi_data_wins_over_kpi_explanation(self, router: IntentRouter) -> None:
        # "chiffre d'affaires" is a live data question, not a definition
        m = router.route("quel est le chiffre d'affaires du magasin 3 ?")
        assert m.intent == Intent.GET_KPI_DATA

    def test_accent_insensitive_matching(self, router: IntentRouter) -> None:
        # Same question with and without accent should yield same intent
        with_accent = router.route("quels sont les différents rôles ?")
        without_accent = router.route("quels sont les differents roles ?")
        assert with_accent.intent == without_accent.intent == Intent.EXPLAIN_RBAC
