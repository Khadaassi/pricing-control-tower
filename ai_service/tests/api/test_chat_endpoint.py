import json
import logging
from contextlib import ExitStack
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.chatbot_messages import (
    CHATBOT_SUPPORTED_SCOPE_MESSAGE,
    CHATBOT_TECHNICAL_ERROR_MESSAGE,
    CHATBOT_UNSUPPORTED_USE_CASE_MESSAGE,
)


def logged_events(caplog: pytest.LogCaptureFixture, event_name: str) -> list[dict]:
    return [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "ai_service.chatbot"
        and json.loads(record.getMessage())["event"] == event_name
    ]


def make_raw_response(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "question": "Peux-tu m'expliquer ce KPI ?",
        "intent": "explain_kpi",
        "selected_tool": "kpi_explanation_tool",
        "status": "routed",
        "answer": "La marge est la différence entre le prix de vente et le coût.",
        "source": "kpi_explanation_tool + llm",
        "llm_used": True,
        "kpis_used": [{"kpi_code": "margin", "label": "Margin", "formula": "revenue - cost"}],
    }
    base.update(overrides)
    return base


class TestChatEndpointHappyPath:
    def test_returns_200_and_maps_orchestrator_response(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        mock_orchestrator.answer_question.return_value = make_raw_response()

        response = client.post("/chat", json={"question": "Peux-tu m'expliquer ce KPI ?"})

        assert response.status_code == 200
        body = response.json()
        assert body["question"] == "Peux-tu m'expliquer ce KPI ?"
        assert body["status"] == "routed"
        assert body["intent"] == "explain_kpi"
        assert body["selected_tool"] == "kpi_explanation_tool"
        assert body["source"] == "kpi_explanation_tool + llm"
        assert body["answer"] == make_raw_response()["answer"]
        assert body["metadata"]["llm_used"] is True
        assert body["metadata"]["kpis_used"] == make_raw_response()["kpis_used"]
        assert body["metadata"]["rules_used"] == []
        assert body["metadata"]["roles_used"] == []
        assert body["metadata"]["error_type"] is None

    def test_calls_orchestrator_with_question_only_when_optional_fields_omitted(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        mock_orchestrator.answer_question.return_value = make_raw_response()

        client.post("/chat", json={"question": "Peux-tu m'expliquer ce KPI ?"})

        mock_orchestrator.answer_question.assert_called_once_with(
            question="Peux-tu m'expliquer ce KPI ?",
            user_email=None,
            store_id=None,
        )

    def test_passes_user_email_and_store_id_to_orchestrator(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        mock_orchestrator.answer_question.return_value = make_raw_response(
            intent="list_store_country_price_mismatches",
            selected_tool="anomaly_tool",
            status="answered",
            source="anomaly_tool",
            answer=[{"anomaly": {"anomaly_type": "PRICE_ABOVE_REFERENCE"}, "explanation": {}}],
        )

        client.post(
            "/chat",
            json={
                "question": "Explique-moi les anomalies de prix.",
                "user_email": "pricing.analyst@example.com",
                "store_id": 42,
            },
        )

        mock_orchestrator.answer_question.assert_called_once_with(
            question="Explique-moi les anomalies de prix.",
            user_email="pricing.analyst@example.com",
            store_id=42,
        )

    def test_answer_can_be_a_list_for_anomaly_results(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        anomalies_answer = [
            {"anomaly": {"anomaly_type": "PRICE_ABOVE_REFERENCE"}, "explanation": {}},
        ]
        mock_orchestrator.answer_question.return_value = make_raw_response(
            intent="list_store_country_price_mismatches",
            selected_tool="anomaly_tool",
            status="answered",
            source="anomaly_tool",
            answer=anomalies_answer,
        )

        response = client.post(
            "/chat",
            json={
                "question": "Explique-moi les anomalies de prix.",
                "user_email": "pricing.analyst@example.com",
                "store_id": 42,
            },
        )

        assert response.status_code == 200
        assert response.json()["answer"] == anomalies_answer


class TestChatEndpointUnsupportedAndErrorCases:
    def test_maps_unsupported_question_response(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        mock_orchestrator.answer_question.return_value = {
            "question": "Raconte-moi une blague.",
            "intent": "unknown",
            "selected_tool": None,
            "status": "unsupported",
            "message": CHATBOT_UNSUPPORTED_USE_CASE_MESSAGE,
            "answer": CHATBOT_SUPPORTED_SCOPE_MESSAGE,
            "source": "orchestrator",
        }

        response = client.post("/chat", json={"question": "Raconte-moi une blague."})

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "unsupported"
        assert body["selected_tool"] is None
        assert body["answer"] == CHATBOT_SUPPORTED_SCOPE_MESSAGE
        assert body["metadata"]["message"] == CHATBOT_UNSUPPORTED_USE_CASE_MESSAGE

    def test_maps_technical_error_response(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        mock_orchestrator.answer_question.return_value = {
            "question": "Peux-tu m'expliquer ce KPI ?",
            "intent": "explain_kpi",
            "selected_tool": "kpi_explanation_tool",
            "status": "error",
            "answer": CHATBOT_TECHNICAL_ERROR_MESSAGE,
            "source": "orchestrator",
            "error_type": "ValueError",
        }

        response = client.post("/chat", json={"question": "Peux-tu m'expliquer ce KPI ?"})

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "error"
        assert body["answer"] == CHATBOT_TECHNICAL_ERROR_MESSAGE
        assert body["metadata"]["error_type"] == "ValueError"


class TestChatEndpointValidation:
    def test_rejects_empty_question(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        response = client.post("/chat", json={"question": ""})

        assert response.status_code == 422
        mock_orchestrator.answer_question.assert_not_called()

    def test_rejects_missing_question(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        response = client.post("/chat", json={})

        assert response.status_code == 422
        mock_orchestrator.answer_question.assert_not_called()

    def test_rejects_question_over_max_length(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        response = client.post("/chat", json={"question": "a" * 1001})

        assert response.status_code == 422
        mock_orchestrator.answer_question.assert_not_called()

    def test_rejects_store_id_below_one(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        response = client.post("/chat", json={"question": "Hello", "store_id": 0})

        assert response.status_code == 422
        mock_orchestrator.answer_question.assert_not_called()

    def test_rejects_non_integer_store_id(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        response = client.post("/chat", json={"question": "Hello", "store_id": "abc"})

        assert response.status_code == 422
        mock_orchestrator.answer_question.assert_not_called()


class TestChatHealthEndpoint:
    @staticmethod
    def _patch_dependencies(*, backend: bool, chromadb: bool, ollama: bool) -> ExitStack:
        stack = ExitStack()
        stack.enter_context(
            patch(
                "app.api.routes.health._check_backend",
                return_value={"status": "ok" if backend else "error", "reachable": backend},
            )
        )
        stack.enter_context(
            patch(
                "app.api.routes.health._check_chromadb",
                return_value={"status": "ok" if chromadb else "error", "reachable": chromadb},
            )
        )
        stack.enter_context(
            patch(
                "app.api.routes.health._check_ollama",
                return_value={"status": "ok" if ollama else "error", "reachable": ollama},
            )
        )
        return stack

    def test_health_endpoint_returns_service_status(self, client: TestClient) -> None:
        response = client.get("/chat/health")

        assert response.status_code == 200
        body = response.json()
        assert body["service"] == "ai_service"
        assert body["component"] == "chatbot"
        assert body["status"] in {"ok", "degraded"}

    def test_status_ok_when_llm_and_all_dependencies_reachable(self, client: TestClient) -> None:
        with self._patch_dependencies(backend=True, chromadb=True, ollama=True):
            response = client.get("/chat/health")

        body = response.json()
        assert body["status"] == "ok"
        assert body["checks"] == {
            "backend": {"status": "ok", "reachable": True},
            "chromadb": {"status": "ok", "reachable": True},
            "ollama": {"status": "ok", "reachable": True},
        }

    def test_status_degraded_when_ollama_unreachable(self, client: TestClient) -> None:
        with self._patch_dependencies(backend=True, chromadb=True, ollama=False):
            response = client.get("/chat/health")

        body = response.json()
        assert body["status"] == "degraded"
        assert body["checks"]["ollama"] == {"status": "error", "reachable": False}

    def test_status_degraded_when_chromadb_unreachable(self, client: TestClient) -> None:
        with self._patch_dependencies(backend=True, chromadb=False, ollama=True):
            response = client.get("/chat/health")

        body = response.json()
        assert body["status"] == "degraded"
        assert body["checks"]["chromadb"] == {"status": "error", "reachable": False}

    def test_status_degraded_when_backend_unreachable(self, client: TestClient) -> None:
        with self._patch_dependencies(backend=False, chromadb=True, ollama=True):
            response = client.get("/chat/health")

        body = response.json()
        assert body["status"] == "degraded"
        assert body["checks"]["backend"] == {"status": "error", "reachable": False}


class TestChatEndpointLogging:
    def test_logs_request_received_and_response_generated(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mock_orchestrator.answer_question.return_value = make_raw_response()
        question = "Peux-tu m'expliquer ce KPI ?"

        with caplog.at_level(logging.INFO):
            response = client.post("/chat", json={"question": question})

        assert response.status_code == 200

        received = logged_events(caplog, "chat_request_received")
        assert len(received) == 1
        assert received[0]["question_length"] == len(question)
        assert received[0]["user_email"] is None
        assert received[0]["store_id"] is None
        assert "request_id" in received[0]

        generated = logged_events(caplog, "chat_response_generated")
        assert len(generated) == 1
        assert generated[0]["request_id"] == received[0]["request_id"]
        assert generated[0]["status"] == "routed"
        assert generated[0]["llm_used"] is True
        assert generated[0]["tools_used"] == ["kpi_explanation_tool"]
        assert generated[0]["kpis_used"] == ["margin"]
        assert generated[0]["latency_ms"] >= 0

        assert logged_events(caplog, "chat_request_failed") == []

    def test_never_logs_the_raw_question_text(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        secret_question = "Mon numéro de carte est 4242 4242 4242 4242, explique ce KPI"
        mock_orchestrator.answer_question.return_value = make_raw_response(
            question=secret_question
        )

        with caplog.at_level(logging.INFO):
            client.post("/chat", json={"question": secret_question})

        for record in caplog.records:
            assert secret_question not in record.getMessage()

    def test_logs_request_failed_on_unexpected_exception(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mock_orchestrator.answer_question.side_effect = RuntimeError("boom")

        with caplog.at_level(logging.INFO):
            response = client.post("/chat", json={"question": "Peux-tu m'expliquer ce KPI ?"})

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "error"
        assert body["answer"] == CHATBOT_TECHNICAL_ERROR_MESSAGE
        assert body["metadata"]["error_type"] == "RuntimeError"

        failed = logged_events(caplog, "chat_request_failed")
        assert len(failed) == 1
        assert failed[0]["error_type"] == "RuntimeError"
        assert failed[0]["error_message"] == "boom"
        assert failed[0]["latency_ms"] >= 0

        assert logged_events(caplog, "chat_response_generated") == []
