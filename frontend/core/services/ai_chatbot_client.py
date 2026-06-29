from __future__ import annotations

import logging
import time
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger("pricing_control_tower.frontend.ai_chatbot_client")


class AiChatbotClientError(Exception):
    """Base exception for AI service chatbot client errors."""


class AiChatbotConnectionError(AiChatbotClientError):
    """Raised when the AI service cannot be reached or times out."""


class AiChatbotResponseError(AiChatbotClientError):
    """Raised when the AI service returns an unexpected response."""


def build_chat_payload(
    question: str,
    user_email: str | None = None,
    store_id: int | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"question": question}

    if user_email:
        payload["user_email"] = user_email

    if isinstance(store_id, int) and store_id > 0:
        payload["store_id"] = store_id

    return payload


def ask_chatbot(
    question: str,
    user_email: str | None = None,
    store_id: int | None = None,
) -> dict[str, Any]:
    """Send a question to the AI service /chat endpoint and return its JSON response."""
    url = f"{settings.AI_SERVICE_BASE_URL.rstrip('/')}/chat"
    payload = build_chat_payload(question, user_email, store_id)
    start_time = time.perf_counter()

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

    except requests.exceptions.ConnectionError as exc:
        log_ai_call_failure(user_email, "Unable to connect to AI service.")
        raise AiChatbotConnectionError("Unable to connect to AI service.") from exc

    except requests.exceptions.Timeout as exc:
        log_ai_call_failure(user_email, "AI service request timed out.")
        raise AiChatbotConnectionError("AI service request timed out.") from exc

    except requests.exceptions.HTTPError as exc:
        log_ai_call_failure(user_email, f"AI service returned an error: {response.status_code}")
        raise AiChatbotResponseError(f"AI service returned an error: {response.status_code}") from exc

    except requests.exceptions.JSONDecodeError as exc:
        log_ai_call_failure(user_email, "AI service returned invalid JSON.")
        raise AiChatbotResponseError("AI service returned invalid JSON.") from exc

    logger.info(
        "AI service call succeeded",
        extra={
            "extra_fields": {
                "event": "ai_service_call_succeeded",
                "status_code": response.status_code,
                "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
                "user_email": user_email,
            }
        },
    )

    return data


def log_ai_call_failure(user_email: str | None, error: str) -> None:
    logger.warning(
        "AI service call failed",
        extra={
            "extra_fields": {
                "event": "ai_service_call_failed",
                "user_email": user_email,
                "error": error,
            }
        },
    )
