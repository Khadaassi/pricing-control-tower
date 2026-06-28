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
from app.orchestrator.chatbot_orchestrator import ChatbotOrchestrator


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
            "roles_used": [{"role_code": "STORE_MANAGER", "label": "Store manager", "scope": "Single store"}],
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
        assert result["answer"] == mock_anomaly_tool.list_store_country_price_mismatches.return_value

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
