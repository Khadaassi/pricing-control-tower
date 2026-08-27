from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import app.api.routes.chat as chat_routes
from app.core.internal_auth import issue_service_token
from app.main import app
from app.orchestrator.chatbot_orchestrator import ChatbotOrchestrator


@pytest.fixture
def client() -> TestClient:
    # POST /chat requires a bearer token (see test_chat_auth.py) — every other
    # test in this package exercises orchestration behavior, not auth, so the
    # client carries a valid token by default rather than making all ~20 call
    # sites in test_chat_endpoint.py pass one individually.
    token = issue_service_token("test-caller")
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


@pytest.fixture
def mock_orchestrator_instance() -> MagicMock:
    return MagicMock(spec=ChatbotOrchestrator)


@pytest.fixture
def mock_orchestrator(
    monkeypatch: pytest.MonkeyPatch,
    mock_orchestrator_instance: MagicMock,
) -> MagicMock:
    monkeypatch.setattr(
        chat_routes,
        "ChatbotOrchestrator",
        MagicMock(return_value=mock_orchestrator_instance),
    )
    return mock_orchestrator_instance
