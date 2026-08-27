import time
from unittest.mock import MagicMock

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.internal_auth import ALGORITHM, issue_service_token
from app.main import app


@pytest.fixture
def unauthenticated_client() -> TestClient:
    return TestClient(app)


class TestChatEndpointRequiresAuthentication:
    def test_missing_authorization_header_returns_401(
        self, unauthenticated_client: TestClient
    ) -> None:
        response = unauthenticated_client.post("/chat", json={"question": "Bonjour"})

        assert response.status_code == 401

    def test_malformed_token_returns_401(self, unauthenticated_client: TestClient) -> None:
        response = unauthenticated_client.post(
            "/chat",
            json={"question": "Bonjour"},
            headers={"Authorization": "Bearer not-a-real-token"},
        )

        assert response.status_code == 401

    def test_token_signed_with_wrong_secret_returns_401(
        self, unauthenticated_client: TestClient
    ) -> None:
        now = int(time.time())
        forged = jwt.encode(
            {"sub": "attacker", "iat": now, "exp": now + 60},
            "wrong-secret",
            algorithm=ALGORITHM,
        )

        response = unauthenticated_client.post(
            "/chat",
            json={"question": "Bonjour"},
            headers={"Authorization": f"Bearer {forged}"},
        )

        assert response.status_code == 401

    def test_expired_token_returns_401(self, unauthenticated_client: TestClient) -> None:
        now = int(time.time())
        expired = jwt.encode(
            {"sub": "test-caller", "iat": now - 120, "exp": now - 60},
            settings.internal_auth_secret,
            algorithm=ALGORITHM,
        )

        response = unauthenticated_client.post(
            "/chat",
            json={"question": "Bonjour"},
            headers={"Authorization": f"Bearer {expired}"},
        )

        assert response.status_code == 401

    def test_token_missing_sub_claim_returns_401(
        self, unauthenticated_client: TestClient
    ) -> None:
        now = int(time.time())
        no_sub = jwt.encode(
            {"iat": now, "exp": now + 60},
            settings.internal_auth_secret,
            algorithm=ALGORITHM,
        )

        response = unauthenticated_client.post(
            "/chat",
            json={"question": "Bonjour"},
            headers={"Authorization": f"Bearer {no_sub}"},
        )

        assert response.status_code == 401

    def test_valid_token_reaches_orchestrator_and_returns_200(
        self,
        unauthenticated_client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import app.api.routes.chat as chat_routes

        mock_instance = MagicMock()
        mock_instance.answer_question.return_value = {
            "question": "Bonjour",
            "intent": "greeting",
            "status": "answered",
            "answer": "Bonjour !",
        }
        monkeypatch.setattr(
            chat_routes, "ChatbotOrchestrator", MagicMock(return_value=mock_instance)
        )

        token = issue_service_token("frontend-service")
        response = unauthenticated_client.post(
            "/chat",
            json={"question": "Bonjour"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "answered"
