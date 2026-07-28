from unittest.mock import MagicMock

import httpx
import pytest

from app.core.chatbot_messages import CHATBOT_TECHNICAL_ERROR_MESSAGE
from app.handlers.rag_response_handler import (
    RAG_INFRA_UNAVAILABLE_ANSWER,
    RAGResponseHandler,
)
from app.orchestrator.chat_context import ChatContext
from app.orchestrator.intent_types import Intent, IntentMatch, RouteType


@pytest.fixture
def ctx() -> ChatContext:
    return ChatContext(
        original_question="Comment fonctionne le calcul de marge ?",
        normalized_question="comment fonctionne le calcul de marge",
        lang="fr",
    )


@pytest.fixture
def match() -> IntentMatch:
    return IntentMatch(intent=Intent.DOCUMENTARY_KNOWLEDGE, route_type=RouteType.RAG)


@pytest.fixture
def handler() -> RAGResponseHandler:
    return RAGResponseHandler(
        document_retriever=MagicMock(),
        llm_provider=MagicMock(),
        prompt_builder=MagicMock(),
        response_service=MagicMock(),
    )


class TestRAGResponseHandlerInfraFailures:
    def test_ollama_connection_error_returns_infra_unavailable_message(
        self, handler: RAGResponseHandler, ctx: ChatContext, match: IntentMatch
    ) -> None:
        handler._document_retriever.search.side_effect = httpx.ConnectError("refused")

        result = handler.handle(ctx, match)

        assert result["status"] == "error"
        assert result["answer"] == RAG_INFRA_UNAVAILABLE_ANSWER
        assert result["error_type"] == "ConnectError"

    def test_chromadb_http_status_error_returns_infra_unavailable_message(
        self, handler: RAGResponseHandler, ctx: ChatContext, match: IntentMatch
    ) -> None:
        request = httpx.Request("POST", "http://chromadb:8000/api/v2/collections/x/query")
        response = httpx.Response(500, request=request)
        handler._document_retriever.search.side_effect = httpx.HTTPStatusError(
            "server error", request=request, response=response
        )

        result = handler.handle(ctx, match)

        assert result["status"] == "error"
        assert result["answer"] == RAG_INFRA_UNAVAILABLE_ANSWER

    def test_unrelated_bug_still_returns_generic_technical_message(
        self, handler: RAGResponseHandler, ctx: ChatContext, match: IntentMatch
    ) -> None:
        handler._document_retriever.search.side_effect = ValueError("unexpected internal bug")

        result = handler.handle(ctx, match)

        assert result["status"] == "error"
        assert result["answer"] == CHATBOT_TECHNICAL_ERROR_MESSAGE
        assert result["answer"] != RAG_INFRA_UNAVAILABLE_ANSWER
