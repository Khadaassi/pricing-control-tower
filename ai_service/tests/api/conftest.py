from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import app.api.routes.chat as chat_routes
from app.main import app
from app.orchestrator.chatbot_orchestrator import ChatbotOrchestrator


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


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
