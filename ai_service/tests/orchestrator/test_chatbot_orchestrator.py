import json
import logging
from unittest.mock import MagicMock

import pytest

from app.core.chatbot_messages import (
    CHATBOT_MISSING_STORE_ID_MESSAGE,
    CHATBOT_MISSING_USER_EMAIL_MESSAGE,
    CHATBOT_NOT_IMPLEMENTED_MESSAGE,
    CHATBOT_SUPPORTED_SCOPE_MESSAGE,
)
from app.core.metrics import get_metric_value
from app.orchestrator.chatbot_orchestrator import (
    ChatbotOrchestrator,
    _RAG_FALLBACK_ANSWER,
)


def logged_events(caplog: pytest.LogCaptureFixture, event_name: str) -> list[dict]:
    return [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "ai_service.orchestrator"
        and json.loads(record.getMessage())["event"] == event_name
    ]


def assert_no_business_tool_was_called(
    mock_kpi_service: MagicMock,
    mock_rbac_service: MagicMock,
    mock_business_rules_service: MagicMock,
    mock_anomaly_tool: MagicMock,
) -> None:
    mock_kpi_service.explain.assert_not_called()
    mock_rbac_service.explain.assert_not_called()
    mock_business_rules_service.explain.assert_not_called()
    mock_anomaly_tool.list_store_country_price_mismatches.assert_not_called()


class TestRouting:
    def test_kpi_question_is_routed_to_kpi_explanation_tool(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question("Peux-tu m'expliquer ce KPI ?")

        assert routed["intent"] == "explain_kpi"
        assert routed["selected_tool"] == "kpi_explanation_tool"

    def test_anomaly_question_is_routed_to_anomaly_tool(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question("Explique-moi les anomalies de prix.")

        assert routed["intent"] == "list_store_country_price_mismatches"
        assert routed["selected_tool"] == "anomaly_tool"

    def test_business_rule_question_is_routed_to_business_rules_tool(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question(
            "Quel est le workflow pour valider un changement de prix ?"
        )

        assert routed["intent"] == "explain_business_rule"
        assert routed["selected_tool"] == "business_rules_tool"

    def test_approve_price_change_question_in_french_is_routed_to_business_rules_tool(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question(
            "Le chatbot peut-il approuver une demande de changement de prix ?"
        )

        assert routed["intent"] == "explain_business_rule"
        assert routed["selected_tool"] == "business_rules_tool"

    def test_rbac_question_is_routed_to_rbac_tool(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question("Que peut faire un store manager ?")

        assert routed["intent"] == "explain_rbac"
        assert routed["selected_tool"] == "rbac_tool"

    def test_unrecognized_question_is_not_routed_to_any_tool(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question("Raconte-moi une blague.")

        assert routed["intent"] == "unknown"
        assert routed["selected_tool"] is None
        assert routed["status"] == "unsupported"


class TestAnswerQuestionDispatch:
    def test_kpi_question_calls_kpi_service(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_kpi_service: MagicMock,
    ) -> None:
        mock_kpi_service.explain.return_value = {
            "answer": "La marge est la différence entre le prix de vente et le coût.",
            "source": "kpi_explanation_tool + llm",
            "kpis_used": [{"kpi_code": "margin", "label": "Margin", "formula": "revenue - cost"}],
            "llm_used": True,
        }

        result = orchestrator.answer_question("Peux-tu m'expliquer ce KPI ?")

        mock_kpi_service.explain.assert_called_once_with("Peux-tu m'expliquer ce KPI ?")
        assert result["selected_tool"] == "kpi_explanation_tool"
        assert result["answer"] == mock_kpi_service.explain.return_value["answer"]

    def test_business_rule_question_calls_business_rules_service(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_business_rules_service: MagicMock,
    ) -> None:
        mock_business_rules_service.explain.return_value = {
            "answer": "Le chatbot ne peut pas approuver une demande de changement de prix.",
            "source": "business_rules_tool + llm",
            "rules_used": [{"rule_code": "chatbot_read_only", "title": "Chatbot read-only rule"}],
            "llm_used": True,
        }

        question = "Quelle est la règle métier pour les changements de prix ?"
        result = orchestrator.answer_question(question)

        mock_business_rules_service.explain.assert_called_once_with(question)
        assert result["selected_tool"] == "business_rules_tool"
        assert result["answer"] == mock_business_rules_service.explain.return_value["answer"]

    def test_rbac_question_calls_rbac_service(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_rbac_service: MagicMock,
    ) -> None:
        mock_rbac_service.explain.return_value = {
            "answer": "Un store manager accède uniquement aux données de son magasin.",
            "source": "rbac_tool + llm",
            "roles_used": [
                {"role_code": "STORE_MANAGER", "label": "Store manager", "scope": "Single store"}
            ],
            "llm_used": True,
        }

        question = "Que peut faire un store manager ?"
        result = orchestrator.answer_question(question)

        mock_rbac_service.explain.assert_called_once_with(question)
        assert result["selected_tool"] == "rbac_tool"
        assert result["answer"] == mock_rbac_service.explain.return_value["answer"]

    def test_anomaly_question_calls_anomaly_tool_with_user_context(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_anomaly_tool: MagicMock,
    ) -> None:
        mock_anomaly_tool.list_store_country_price_mismatches.return_value = [
            {"anomaly": {"anomaly_type": "PRICE_ABOVE_REFERENCE"}, "explanation": {}},
        ]

        result = orchestrator.answer_question(
            "Explique-moi les anomalies de prix.",
            user_email="user@example.com",
            store_id=42,
        )

        mock_anomaly_tool.list_store_country_price_mismatches.assert_called_once_with(
            user_email="user@example.com",
            store_id=42,
        )
        assert result["status"] == "answered"
        assert result["selected_tool"] == "anomaly_tool"
        assert (
            result["answer"]
            == mock_anomaly_tool.list_store_country_price_mismatches.return_value
        )

    def test_anomaly_question_without_user_email_does_not_call_anomaly_tool(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_anomaly_tool: MagicMock,
    ) -> None:
        result = orchestrator.answer_question(
            "Explique-moi les anomalies de prix.",
            store_id=42,
        )

        mock_anomaly_tool.list_store_country_price_mismatches.assert_not_called()
        assert result["status"] == "missing_context"
        assert result["answer"] == CHATBOT_MISSING_USER_EMAIL_MESSAGE

    def test_anomaly_question_without_store_id_does_not_call_anomaly_tool(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_anomaly_tool: MagicMock,
    ) -> None:
        result = orchestrator.answer_question(
            "Explique-moi les anomalies de prix.",
            user_email="user@example.com",
        )

        mock_anomaly_tool.list_store_country_price_mismatches.assert_not_called()
        assert result["status"] == "missing_context"
        assert result["answer"] == CHATBOT_MISSING_STORE_ID_MESSAGE

    def test_unrecognized_question_calls_no_business_tool(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_kpi_service: MagicMock,
        mock_rbac_service: MagicMock,
        mock_business_rules_service: MagicMock,
        mock_anomaly_tool: MagicMock,
    ) -> None:
        result = orchestrator.answer_question("Raconte-moi une blague.")

        assert result["status"] == "unsupported"
        assert result["answer"] == CHATBOT_SUPPORTED_SCOPE_MESSAGE
        assert_no_business_tool_was_called(
            mock_kpi_service, mock_rbac_service, mock_business_rules_service, mock_anomaly_tool
        )


class TestGuardrails:
    """The chatbot is read-only: even when a question asks for an action, the
    orchestrator must only ever call the `.explain(...)` (read) entry point of a
    service, never an action that would create/approve/reject/apply a price change.
    """

    def test_chatbot_approval_request_is_explained_not_executed(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_business_rules_service: MagicMock,
        mock_anomaly_tool: MagicMock,
    ) -> None:
        mock_business_rules_service.explain.return_value = {
            "answer": "Le chatbot est en lecture seule et ne peut pas approuver de demande.",
            "source": "business_rules_tool + llm",
            "rules_used": [{"rule_code": "chatbot_read_only", "title": "Chatbot read-only rule"}],
            "llm_used": True,
        }

        question = "Can the chatbot approve a price change request?"
        result = orchestrator.answer_question(question)

        assert result["intent"] == "explain_business_rule"
        mock_business_rules_service.explain.assert_called_once_with(question)
        mock_anomaly_tool.list_store_country_price_mismatches.assert_not_called()
        # BusinessRulesExplanationService only exposes `explain` (read-only) on
        # its real spec, so MagicMock(spec=...) would reject any write-style call.
        assert mock_business_rules_service.method_calls == [("explain", (question,), {})]

    def test_direct_action_request_triggers_no_tool_call(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_kpi_service: MagicMock,
        mock_rbac_service: MagicMock,
        mock_business_rules_service: MagicMock,
        mock_anomaly_tool: MagicMock,
    ) -> None:
        # No keyword maps this phrasing to a known intent, so it falls back to
        # "unknown" and the orchestrator answers with the generic scope message
        # instead of attempting any write action (the chatbot has no write
        # capability in the first place, but no read tool is touched either).
        result = orchestrator.answer_question("Approuve cette demande de changement de prix")

        assert result["status"] == "unsupported"
        assert result["answer"] == CHATBOT_SUPPORTED_SCOPE_MESSAGE
        assert_no_business_tool_was_called(
            mock_kpi_service, mock_rbac_service, mock_business_rules_service, mock_anomaly_tool
        )


class TestRevenueIntentNotYetWired:
    """`get_country_revenue` is detected and routed to `kpi_tool`, but
    `answer_question` has no handler for it yet: it falls through to the
    generic "not implemented" response without calling `kpi_service.explain`.
    """

    def test_revenue_question_is_routed_but_answered_as_not_implemented(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_kpi_service: MagicMock,
    ) -> None:
        result = orchestrator.answer_question("What is our total revenue?")

        assert result["intent"] == "get_country_revenue"
        assert result["selected_tool"] == "kpi_tool"
        assert result["status"] == "not_implemented"
        assert result["answer"] == CHATBOT_NOT_IMPLEMENTED_MESSAGE
        mock_kpi_service.explain.assert_not_called()


class TestLogging:
    def test_logs_chat_tool_selected_for_a_recognized_question(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_rbac_service: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mock_rbac_service.explain.return_value = {
            "answer": "...",
            "source": "rbac_tool + llm",
            "roles_used": [],
            "llm_used": True,
        }

        with caplog.at_level(logging.INFO):
            orchestrator.answer_question(
                "Que peut faire un store manager ?",
                user_email="user@example.com",
                store_id=42,
            )

        events = logged_events(caplog, "chat_tool_selected")
        assert len(events) == 1
        assert events[0]["intent"] == "explain_rbac"
        assert events[0]["tool_name"] == "rbac_tool"
        assert events[0]["user_email_present"] is True
        assert events[0]["store_id_present"] is True

    def test_logs_tool_name_none_for_unrecognized_question(
        self,
        orchestrator: ChatbotOrchestrator,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        with caplog.at_level(logging.INFO):
            orchestrator.answer_question("Raconte-moi une blague.")

        events = logged_events(caplog, "chat_tool_selected")
        assert len(events) == 1
        assert events[0]["intent"] == "unknown"
        assert events[0]["tool_name"] == "none"
        assert events[0]["user_email_present"] is False
        assert events[0]["store_id_present"] is False


class TestToolUsageMetrics:
    """`chat_tool_usage_total` is incremented at the same call site as the
    `chat_tool_selected` log, so it is exercised here rather than through the
    `/chat` endpoint tests, which mock the whole orchestrator and never reach
    this code path.
    """

    def test_recognized_question_increments_tool_usage_for_its_tool(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_rbac_service: MagicMock,
    ) -> None:
        mock_rbac_service.explain.return_value = {
            "answer": "...",
            "source": "rbac_tool + llm",
            "roles_used": [],
            "llm_used": True,
        }

        orchestrator.answer_question("Que peut faire un store manager ?")

        assert get_metric_value(
            "ai_chat_tool_usage_total", {"tool_name": "rbac_tool"}
        ) == 1.0

    def test_unrecognized_question_increments_tool_usage_for_none(
        self,
        orchestrator: ChatbotOrchestrator,
    ) -> None:
        orchestrator.answer_question("Raconte-moi une blague.")

        assert get_metric_value(
            "ai_chat_tool_usage_total", {"tool_name": "none"}
        ) == 1.0

    def test_each_call_adds_to_the_running_total(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_rbac_service: MagicMock,
    ) -> None:
        mock_rbac_service.explain.return_value = {
            "answer": "...",
            "source": "rbac_tool + llm",
            "roles_used": [],
            "llm_used": True,
        }

        orchestrator.answer_question("Que peut faire un store manager ?")
        orchestrator.answer_question("Que peut faire un store manager ?")
        orchestrator.answer_question("Raconte-moi une blague.")

        assert get_metric_value(
            "ai_chat_tool_usage_total", {"tool_name": "rbac_tool"}
        ) == 2.0
        assert get_metric_value(
            "ai_chat_tool_usage_total", {"tool_name": "none"}
        ) == 1.0


# ---------------------------------------------------------------------------
# RAG — Documentary knowledge routing
# ---------------------------------------------------------------------------

_SAMPLE_CHUNK = {
    "text": "Store managers can only access their own store data.",
    "source_file": "docs/01_functional/rbac_roles_permissions.md",
    "section_title": "STORE_MANAGER",
    "domain": "rbac",
    "score": 0.82,
}

_MONITORING_CHUNK = {
    "text": "The chatbot is monitored via Prometheus and Grafana dashboards.",
    "source_file": "docs/04_monitoring/monitoring_setup.md",
    "section_title": "Chatbot Observability",
    "domain": "monitoring",
    "score": 0.78,
}

_WORKFLOW_CHUNK = {
    "text": "A price change goes through DRAFT → PENDING → APPROVED → APPLIED.",
    "source_file": "docs/03_architecture/pricing_workflow.md",
    "section_title": "Workflow Statuses",
    "domain": "architecture",
    "score": 0.76,
}


class TestDocumentaryKnowledgeRouting:
    def test_monitoring_question_routes_to_documentary_knowledge(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question("How is the chatbot monitored?")

        assert routed["intent"] == "documentary_knowledge"
        assert routed["selected_tool"] == "rag_retriever"

    def test_architecture_question_routes_to_documentary_knowledge(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question(
            "What does the pricing architecture documentation describe?"
        )

        assert routed["intent"] == "documentary_knowledge"
        assert routed["selected_tool"] == "rag_retriever"

    def test_runbook_question_routes_to_documentary_knowledge(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question("Is there a runbook for this system?")

        assert routed["intent"] == "documentary_knowledge"
        assert routed["selected_tool"] == "rag_retriever"

    def test_chatbot_capabilities_question_routes_to_documentary_knowledge(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question("What can the chatbot do?")

        assert routed["intent"] == "documentary_knowledge"
        assert routed["selected_tool"] == "rag_retriever"

    def test_authorization_documentation_question_routes_to_documentary_knowledge(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        # "authorization" contains none of the RBAC keywords (role, permission,
        # store manager, rbac, access…); "documentation" triggers documentary_knowledge.
        routed = orchestrator.route_question(
            "What does the authorization documentation describe?"
        )

        assert routed["intent"] == "documentary_knowledge"
        assert routed["selected_tool"] == "rag_retriever"

    def test_observability_question_routes_to_documentary_knowledge(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question("What is the observability strategy?")

        assert routed["intent"] == "documentary_knowledge"
        assert routed["selected_tool"] == "rag_retriever"


class TestDocumentaryKnowledgeAnswering:
    def test_documentary_question_calls_document_retriever(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_document_retriever: MagicMock,
        mock_llm_provider: MagicMock,
    ) -> None:
        mock_document_retriever.search.return_value = [_SAMPLE_CHUNK]
        mock_llm_provider.generate_response.return_value = (
            "Store managers can only view their own store."
        )

        orchestrator.answer_question("What does the authorization documentation describe?")

        mock_document_retriever.search.assert_called_once()

    def test_documentary_question_calls_llm_with_context(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_document_retriever: MagicMock,
        mock_llm_provider: MagicMock,
    ) -> None:
        mock_document_retriever.search.return_value = [_SAMPLE_CHUNK]
        mock_llm_provider.generate_response.return_value = "Store managers are scoped."

        orchestrator.answer_question("What does the authorization documentation describe?")

        mock_llm_provider.generate_response.assert_called_once()
        prompt = mock_llm_provider.generate_response.call_args[0][0]
        assert "rbac_roles_permissions.md" in prompt

    def test_documentary_response_includes_rag_sources(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_document_retriever: MagicMock,
        mock_llm_provider: MagicMock,
    ) -> None:
        mock_document_retriever.search.return_value = [_SAMPLE_CHUNK]
        mock_llm_provider.generate_response.return_value = "Store managers are scoped."

        result = orchestrator.answer_question(
            "What does the authorization documentation describe?"
        )

        assert result["source"] == "rag_retriever"
        assert result["status"] == "answered"
        assert len(result["rag_sources"]) == 1
        assert result["rag_sources"][0]["source_file"] == "docs/01_functional/rbac_roles_permissions.md"
        assert result["rag_sources"][0]["section_title"] == "STORE_MANAGER"

    def test_monitoring_question_calls_rag_and_returns_monitoring_source(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_document_retriever: MagicMock,
        mock_llm_provider: MagicMock,
    ) -> None:
        mock_document_retriever.search.return_value = [_MONITORING_CHUNK]
        mock_llm_provider.generate_response.return_value = (
            "The chatbot is monitored via Prometheus."
        )

        result = orchestrator.answer_question("How is the chatbot monitored?")

        mock_document_retriever.search.assert_called_once()
        assert result["source"] == "rag_retriever"
        assert any(
            "monitoring_setup.md" in s["source_file"] for s in result["rag_sources"]
        )

    def test_workflow_documentation_question_calls_rag_without_backend(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_document_retriever: MagicMock,
        mock_llm_provider: MagicMock,
        mock_anomaly_tool: MagicMock,
        mock_rbac_service: MagicMock,
        mock_business_rules_service: MagicMock,
    ) -> None:
        mock_document_retriever.search.return_value = [_WORKFLOW_CHUNK]
        mock_llm_provider.generate_response.return_value = (
            "The workflow goes through DRAFT → PENDING → APPROVED → APPLIED."
        )

        result = orchestrator.answer_question("What does the pricing architecture documentation describe?")

        mock_document_retriever.search.assert_called_once()
        mock_anomaly_tool.list_store_country_price_mismatches.assert_not_called()
        mock_rbac_service.explain.assert_not_called()
        mock_business_rules_service.explain.assert_not_called()
        assert result["source"] == "rag_retriever"
        assert any(
            "pricing_workflow.md" in s["source_file"] for s in result["rag_sources"]
        )

    def test_low_score_chunks_trigger_fallback_answer(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_document_retriever: MagicMock,
        mock_llm_provider: MagicMock,
    ) -> None:
        low_score_chunk = {**_SAMPLE_CHUNK, "score": 0.10}
        mock_document_retriever.search.return_value = [low_score_chunk]

        result = orchestrator.answer_question("What does the authorization documentation describe?")

        mock_llm_provider.generate_response.assert_not_called()
        assert result["answer"] == _RAG_FALLBACK_ANSWER
        assert result["rag_sources"] == []
        assert result["llm_used"] is False

    def test_empty_retriever_results_trigger_fallback_answer(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_document_retriever: MagicMock,
        mock_llm_provider: MagicMock,
    ) -> None:
        mock_document_retriever.search.return_value = []

        result = orchestrator.answer_question("How is the chatbot monitored?")

        mock_llm_provider.generate_response.assert_not_called()
        assert result["answer"] == _RAG_FALLBACK_ANSWER

    def test_retriever_exception_returns_error_response(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_document_retriever: MagicMock,
    ) -> None:
        mock_document_retriever.search.side_effect = RuntimeError("Chroma unreachable")

        result = orchestrator.answer_question("How is the chatbot monitored?")

        assert result["status"] == "error"
        assert result["error_type"] == "RuntimeError"


# ---------------------------------------------------------------------------
# Non-regression: operational questions must NOT trigger RAG
# ---------------------------------------------------------------------------


class TestRAGNonRegression:
    def test_revenue_question_does_not_call_document_retriever(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_document_retriever: MagicMock,
    ) -> None:
        result = orchestrator.answer_question("What is our total revenue?")

        mock_document_retriever.search.assert_not_called()
        assert result["intent"] == "get_country_revenue"

    def test_operational_anomaly_question_does_not_call_document_retriever(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_document_retriever: MagicMock,
    ) -> None:
        result = orchestrator.answer_question(
            "Explique-moi les anomalies de prix.",
            user_email="user@example.com",
            store_id=1,
        )

        mock_document_retriever.search.assert_not_called()
        assert result["intent"] == "list_store_country_price_mismatches"

    def test_rbac_question_routes_to_rbac_tool_not_rag(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_rbac_service: MagicMock,
        mock_document_retriever: MagicMock,
    ) -> None:
        mock_rbac_service.explain.return_value = {
            "answer": "Un store manager accède uniquement à son magasin.",
            "source": "rbac_tool + llm",
            "roles_used": [],
            "llm_used": True,
        }

        result = orchestrator.answer_question("Que peut faire un store manager ?")

        mock_rbac_service.explain.assert_called_once()
        mock_document_retriever.search.assert_not_called()
        assert result["intent"] == "explain_rbac"

    def test_business_rule_question_routes_to_business_rules_tool_not_rag(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_business_rules_service: MagicMock,
        mock_document_retriever: MagicMock,
    ) -> None:
        mock_business_rules_service.explain.return_value = {
            "answer": "Le chatbot est en lecture seule.",
            "source": "business_rules_tool + llm",
            "rules_used": [],
            "llm_used": True,
        }

        result = orchestrator.answer_question(
            "Quel est le workflow pour valider un changement de prix ?"
        )

        mock_business_rules_service.explain.assert_called_once()
        mock_document_retriever.search.assert_not_called()
        assert result["intent"] == "explain_business_rule"

    def test_kpi_question_routes_to_kpi_tool_not_rag(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_kpi_service: MagicMock,
        mock_document_retriever: MagicMock,
    ) -> None:
        mock_kpi_service.explain.return_value = {
            "answer": "La marge est la différence entre prix de vente et coût.",
            "source": "kpi_explanation_tool + llm",
            "kpis_used": [],
            "llm_used": True,
        }

        result = orchestrator.answer_question("Peux-tu m'expliquer ce KPI ?")

        mock_kpi_service.explain.assert_called_once()
        mock_document_retriever.search.assert_not_called()
        assert result["intent"] == "explain_kpi"

    def test_direct_action_request_does_not_call_document_retriever(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_document_retriever: MagicMock,
    ) -> None:
        result = orchestrator.answer_question("Approuve cette demande de changement de prix")

        mock_document_retriever.search.assert_not_called()
        assert result["status"] == "unsupported"

    def test_rag_tool_usage_metric_is_incremented_for_documentary_question(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_document_retriever: MagicMock,
        mock_llm_provider: MagicMock,
    ) -> None:
        mock_document_retriever.search.return_value = [_MONITORING_CHUNK]
        mock_llm_provider.generate_response.return_value = "Monitored via Prometheus."

        orchestrator.answer_question("How is the chatbot monitored?")

        assert get_metric_value(
            "ai_chat_tool_usage_total", {"tool_name": "rag_retriever"}
        ) == 1.0


# ---------------------------------------------------------------------------
# T198 — Source references in RAG responses
# ---------------------------------------------------------------------------

_DUPLICATE_CHUNK = {
    "text": "Additional context from the same section.",
    "source_file": "docs/01_functional/rbac_roles_permissions.md",
    "section_title": "STORE_MANAGER",
    "domain": "rbac",
    "score": 0.79,
}


class TestSourceReferences:
    def test_rag_sources_include_title_field(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_document_retriever: MagicMock,
        mock_llm_provider: MagicMock,
    ) -> None:
        mock_document_retriever.search.return_value = [_SAMPLE_CHUNK]
        mock_llm_provider.generate_response.return_value = "Store managers are scoped."

        result = orchestrator.answer_question(
            "What does the authorization documentation describe?"
        )

        assert "title" in result["rag_sources"][0]
        assert result["rag_sources"][0]["title"] == "Rbac Roles Permissions"

    def test_rag_answer_contains_sources_block(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_document_retriever: MagicMock,
        mock_llm_provider: MagicMock,
    ) -> None:
        mock_document_retriever.search.return_value = [_SAMPLE_CHUNK]
        mock_llm_provider.generate_response.return_value = "Store managers are scoped."

        result = orchestrator.answer_question(
            "What does the authorization documentation describe?"
        )

        assert "Documentary sources:" in result["answer"]
        assert "Rbac Roles Permissions" in result["answer"]

    def test_sources_block_shows_section_title(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_document_retriever: MagicMock,
        mock_llm_provider: MagicMock,
    ) -> None:
        mock_document_retriever.search.return_value = [_SAMPLE_CHUNK]
        mock_llm_provider.generate_response.return_value = "Store managers are scoped."

        result = orchestrator.answer_question(
            "What does the authorization documentation describe?"
        )

        assert "STORE_MANAGER" in result["answer"]

    def test_duplicate_chunks_deduplicated_in_rag_sources(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_document_retriever: MagicMock,
        mock_llm_provider: MagicMock,
    ) -> None:
        mock_document_retriever.search.return_value = [_SAMPLE_CHUNK, _DUPLICATE_CHUNK]
        mock_llm_provider.generate_response.return_value = "Store managers are scoped."

        result = orchestrator.answer_question(
            "What does the authorization documentation describe?"
        )

        assert len(result["rag_sources"]) == 1

    def test_duplicate_chunks_deduplicated_in_sources_block(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_document_retriever: MagicMock,
        mock_llm_provider: MagicMock,
    ) -> None:
        mock_document_retriever.search.return_value = [_SAMPLE_CHUNK, _DUPLICATE_CHUNK]
        mock_llm_provider.generate_response.return_value = "Store managers are scoped."

        result = orchestrator.answer_question(
            "What does the authorization documentation describe?"
        )

        # "STORE_MANAGER" must appear exactly once in the sources block
        sources_block_start = result["answer"].find("Documentary sources:")
        sources_section = result["answer"][sources_block_start:]
        assert sources_section.count("STORE_MANAGER") == 1

    def test_sources_block_appended_after_llm_answer(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_document_retriever: MagicMock,
        mock_llm_provider: MagicMock,
    ) -> None:
        mock_document_retriever.search.return_value = [_SAMPLE_CHUNK]
        mock_llm_provider.generate_response.return_value = "LLM answer here."

        result = orchestrator.answer_question(
            "What does the authorization documentation describe?"
        )

        answer = result["answer"]
        llm_part_end = answer.index("Documentary sources:")
        assert "LLM answer here." in answer[:llm_part_end]

    def test_fallback_answer_has_no_sources_block(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_document_retriever: MagicMock,
        mock_llm_provider: MagicMock,
    ) -> None:
        mock_document_retriever.search.return_value = []

        result = orchestrator.answer_question("How is the chatbot monitored?")

        assert "Documentary sources:" not in result["answer"]
        assert result["rag_sources"] == []

    def test_tool_calling_response_has_no_rag_sources(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_rbac_service: MagicMock,
        mock_document_retriever: MagicMock,
    ) -> None:
        mock_rbac_service.explain.return_value = {
            "answer": "Un store manager accède uniquement à son magasin.",
            "source": "rbac_tool + llm",
            "roles_used": [],
            "llm_used": True,
        }

        result = orchestrator.answer_question("Que peut faire un store manager ?")

        mock_document_retriever.search.assert_not_called()
        assert "rag_sources" not in result or result.get("rag_sources", []) == []
        assert "Documentary sources:" not in str(result.get("answer", ""))


# ---------------------------------------------------------------------------
# T199 — Reference data tool (countries, stores, products, product families)
# ---------------------------------------------------------------------------


class TestReferenceDataRouting:
    def test_list_countries_routes_to_reference_data_tool(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question("List countries")

        assert routed["intent"] == "reference_data"
        assert routed["selected_tool"] == "reference_data_tool"

    def test_what_stores_are_available_routes_to_reference_data_tool(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question("What stores are available?")

        assert routed["intent"] == "reference_data"
        assert routed["selected_tool"] == "reference_data_tool"

    def test_show_product_families_routes_to_reference_data_tool(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question("Show me the product families")

        assert routed["intent"] == "reference_data"
        assert routed["selected_tool"] == "reference_data_tool"

    def test_list_active_products_routes_to_reference_data_tool(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question("List active products")

        assert routed["intent"] == "reference_data"
        assert routed["selected_tool"] == "reference_data_tool"

    def test_french_stores_question_routes_to_reference_data_tool(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question("Quels magasins existent ?")

        assert routed["intent"] == "reference_data"
        assert routed["selected_tool"] == "reference_data_tool"

    def test_french_product_families_question_routes_to_reference_data_tool(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question("Quelles sont les familles de produits ?")

        assert routed["intent"] == "reference_data"
        assert routed["selected_tool"] == "reference_data_tool"

    def test_documentary_pricing_rule_question_does_not_route_to_reference_data(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question("How does the price change workflow work?")

        assert routed["intent"] != "reference_data"

    def test_anomaly_question_does_not_route_to_reference_data(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question("Explique-moi les anomalies de prix.")

        assert routed["intent"] != "reference_data"

    def test_revenue_question_does_not_route_to_reference_data(
        self, orchestrator: ChatbotOrchestrator
    ) -> None:
        routed = orchestrator.route_question("What is our total revenue?")

        assert routed["intent"] != "reference_data"


class TestReferenceDataAnswering:
    def test_list_countries_calls_reference_data_tool(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_reference_data_tool: MagicMock,
    ) -> None:
        mock_reference_data_tool.list_countries.return_value = [
            {"id": 1, "code": "FR", "name": "France"}
        ]

        result = orchestrator.answer_question("List countries")

        mock_reference_data_tool.list_countries.assert_called_once()
        assert result["status"] == "answered"
        assert result["source"] == "reference_data_tool"
        assert "France" in result["answer"]

    def test_list_stores_calls_reference_data_tool(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_reference_data_tool: MagicMock,
    ) -> None:
        mock_reference_data_tool.list_stores.return_value = [
            {"id": 1, "code": "LIL", "name": "Lille Centre", "country_id": 1}
        ]

        result = orchestrator.answer_question("What stores are available?")

        mock_reference_data_tool.list_stores.assert_called_once()
        assert result["status"] == "answered"
        assert "Lille Centre" in result["answer"]

    def test_list_product_families_calls_reference_data_tool(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_reference_data_tool: MagicMock,
    ) -> None:
        mock_reference_data_tool.list_product_families.return_value = [
            {"id": 1, "code": "RUN", "name": "Running"},
            {"id": 2, "code": "HIK", "name": "Hiking"},
        ]

        result = orchestrator.answer_question("Show me the product families")

        mock_reference_data_tool.list_product_families.assert_called_once()
        assert result["status"] == "answered"
        assert "Running" in result["answer"]
        assert "Hiking" in result["answer"]

    def test_list_active_products_passes_active_filter(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_reference_data_tool: MagicMock,
    ) -> None:
        mock_reference_data_tool.list_products.return_value = [
            {"id": 1, "code": "RUN-001", "name": "Running Shoes", "active": True}
        ]

        result = orchestrator.answer_question("List active products")

        mock_reference_data_tool.list_products.assert_called_once_with(
            active=True, user_email=None
        )
        assert result["status"] == "answered"
        assert "RUN-001" in result["answer"]

    def test_empty_countries_returns_no_data_found_message(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_reference_data_tool: MagicMock,
    ) -> None:
        mock_reference_data_tool.list_countries.return_value = []

        result = orchestrator.answer_question("List countries")

        assert result["status"] == "answered"
        assert result["answer"] == "No matching reference data was found."

    def test_reference_data_tool_exception_returns_error_response(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_reference_data_tool: MagicMock,
    ) -> None:
        mock_reference_data_tool.list_countries.side_effect = RuntimeError("Backend unreachable")

        result = orchestrator.answer_question("List countries")

        assert result["status"] == "error"
        assert result["error_type"] == "RuntimeError"


class TestReferenceDataRAGNonRegression:
    def test_reference_data_question_does_not_call_document_retriever(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_reference_data_tool: MagicMock,
        mock_document_retriever: MagicMock,
    ) -> None:
        mock_reference_data_tool.list_countries.return_value = [
            {"id": 1, "code": "FR", "name": "France"}
        ]

        orchestrator.answer_question("List countries")

        mock_document_retriever.search.assert_not_called()

    def test_store_manager_rbac_question_does_not_route_to_reference_data(
        self,
        orchestrator: ChatbotOrchestrator,
        mock_reference_data_tool: MagicMock,
        mock_rbac_service: MagicMock,
    ) -> None:
        mock_rbac_service.explain.return_value = {
            "answer": "Un store manager accède uniquement à son magasin.",
            "source": "rbac_tool + llm",
            "roles_used": [],
            "llm_used": True,
        }

        result = orchestrator.answer_question("Que peut faire un store manager ?")

        mock_reference_data_tool.list_stores.assert_not_called()
        assert result["intent"] == "explain_rbac"
