from unittest.mock import MagicMock

import httpx
import pytest

from app.core.chatbot_messages import CHATBOT_RBAC_DENIED_MESSAGE, CHATBOT_TECHNICAL_ERROR_MESSAGE
from app.handlers.tool_response_handler import ToolResponseHandler
from app.orchestrator.chat_context import ChatContext
from app.orchestrator.intent_types import Intent, IntentMatch, RouteType


@pytest.fixture
def ctx() -> ChatContext:
    return ChatContext(
        original_question="liste les pays",
        normalized_question="liste les pays",
        user_email="user@pct.local",
        lang="fr",
    )


@pytest.fixture
def match() -> IntentMatch:
    return IntentMatch(intent=Intent.REFERENCE_DATA, route_type=RouteType.TOOL)


@pytest.fixture
def handler() -> ToolResponseHandler:
    return ToolResponseHandler(
        business_rules_service=MagicMock(),
        rbac_service=MagicMock(),
        anomaly_tool=MagicMock(),
        kpi_service=MagicMock(),
        kpi_data_tool=MagicMock(),
        price_change_request_tool=MagicMock(),
        promotion_tool=MagicMock(),
        price_tool=MagicMock(),
        reference_data_tool=MagicMock(),
        response_service=MagicMock(),
    )


def _http_status_error(status_code: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "http://backend:8000/countries")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError("error", request=request, response=response)


class TestToolResponseHandlerRbacVsTechnicalErrors:
    def test_401_from_backend_returns_rbac_message(
        self, handler: ToolResponseHandler, ctx: ChatContext, match: IntentMatch
    ) -> None:
        handler._reference_data_tool.list_countries.side_effect = _http_status_error(401)

        result = handler.handle(ctx, match)

        assert result["status"] == "error"
        assert result["answer"] == CHATBOT_RBAC_DENIED_MESSAGE
        assert result["error_type"] == "HTTPStatusError"

    def test_403_from_backend_returns_rbac_message(
        self, handler: ToolResponseHandler, ctx: ChatContext, match: IntentMatch
    ) -> None:
        handler._reference_data_tool.list_countries.side_effect = _http_status_error(403)

        result = handler.handle(ctx, match)

        assert result["status"] == "error"
        assert result["answer"] == CHATBOT_RBAC_DENIED_MESSAGE

    def test_500_from_backend_returns_generic_technical_message(
        self, handler: ToolResponseHandler, ctx: ChatContext, match: IntentMatch
    ) -> None:
        handler._reference_data_tool.list_countries.side_effect = _http_status_error(500)

        result = handler.handle(ctx, match)

        assert result["status"] == "error"
        assert result["answer"] == CHATBOT_TECHNICAL_ERROR_MESSAGE
        assert result["answer"] != CHATBOT_RBAC_DENIED_MESSAGE

    def test_connection_error_returns_generic_technical_message(
        self, handler: ToolResponseHandler, ctx: ChatContext, match: IntentMatch
    ) -> None:
        handler._reference_data_tool.list_countries.side_effect = httpx.ConnectError("refused")

        result = handler.handle(ctx, match)

        assert result["status"] == "error"
        assert result["answer"] == CHATBOT_TECHNICAL_ERROR_MESSAGE

    def test_unrelated_bug_returns_generic_technical_message(
        self, handler: ToolResponseHandler, ctx: ChatContext, match: IntentMatch
    ) -> None:
        handler._reference_data_tool.list_countries.side_effect = ValueError("unexpected bug")

        result = handler.handle(ctx, match)

        assert result["status"] == "error"
        assert result["answer"] == CHATBOT_TECHNICAL_ERROR_MESSAGE
