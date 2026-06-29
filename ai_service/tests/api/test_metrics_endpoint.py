from typing import Any
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from prometheus_client import CONTENT_TYPE_LATEST


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


class TestMetricsEndpointShape:
    def test_returns_200_with_prometheus_content_type(self, client: TestClient) -> None:
        response = client.get("/metrics")

        assert response.status_code == 200
        assert response.headers["content-type"] == CONTENT_TYPE_LATEST

    def test_response_contains_all_expected_metric_names(self, client: TestClient) -> None:
        body = client.get("/metrics").text

        assert "ai_chat_requests_total" in body
        assert "ai_chat_responses_total" in body
        assert "ai_chat_errors_total" in body
        assert "ai_chat_response_latency_seconds" in body
        assert "ai_chat_tool_usage_total" in body


class TestChatRequestMetrics:
    def test_chat_request_increments_chat_requests_total(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        mock_orchestrator.answer_question.return_value = make_raw_response()

        client.post("/chat", json={"question": "Peux-tu m'expliquer ce KPI ?"})
        client.post("/chat", json={"question": "Peux-tu m'expliquer ce KPI ?"})

        body = client.get("/metrics").text
        assert "ai_chat_requests_total 2.0" in body

    def test_validation_error_does_not_increment_chat_requests_total(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        client.post("/chat", json={"question": ""})

        body = client.get("/metrics").text
        assert "ai_chat_requests_total 0.0" in body
        mock_orchestrator.answer_question.assert_not_called()

    def test_successful_chat_increments_responses_total_by_status(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        mock_orchestrator.answer_question.return_value = make_raw_response(status="routed")

        client.post("/chat", json={"question": "Peux-tu m'expliquer ce KPI ?"})

        body = client.get("/metrics").text
        assert 'ai_chat_responses_total{status="routed"} 1.0' in body

    def test_unsupported_chat_increments_responses_total_for_unsupported(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        mock_orchestrator.answer_question.return_value = {
            "question": "Raconte-moi une blague.",
            "intent": "unknown",
            "selected_tool": None,
            "status": "unsupported",
            "answer": "Je ne peux pas répondre à cette question.",
            "source": "orchestrator",
        }

        client.post("/chat", json={"question": "Raconte-moi une blague."})

        body = client.get("/metrics").text
        assert 'ai_chat_responses_total{status="unsupported"} 1.0' in body

    def test_unexpected_exception_increments_errors_and_responses_total(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        mock_orchestrator.answer_question.side_effect = RuntimeError("boom")

        client.post("/chat", json={"question": "Peux-tu m'expliquer ce KPI ?"})

        body = client.get("/metrics").text
        assert 'ai_chat_errors_total{error_type="RuntimeError"} 1.0' in body
        assert 'ai_chat_responses_total{status="error"} 1.0' in body

    def test_chat_request_records_latency(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        mock_orchestrator.answer_question.return_value = make_raw_response()

        client.post("/chat", json={"question": "Peux-tu m'expliquer ce KPI ?"})

        body = client.get("/metrics").text
        assert "ai_chat_response_latency_seconds_count 1.0" in body

    def test_latency_is_recorded_even_when_the_request_fails(
        self,
        client: TestClient,
        mock_orchestrator: MagicMock,
    ) -> None:
        mock_orchestrator.answer_question.side_effect = RuntimeError("boom")

        client.post("/chat", json={"question": "Peux-tu m'expliquer ce KPI ?"})

        body = client.get("/metrics").text
        assert "ai_chat_response_latency_seconds_count 1.0" in body
