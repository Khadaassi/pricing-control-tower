from __future__ import annotations

import logging
from typing import Any

from django.conf import settings

from services.http import do_request

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

    return do_request(
        "POST",
        url,
        service_label="AI service",
        connection_error_cls=AiChatbotConnectionError,
        response_error_cls=AiChatbotResponseError,
        json=payload,
        timeout=30,
        on_success=lambda status_code, duration_ms: logger.info(
            "AI service call succeeded",
            extra={
                "extra_fields": {
                    "event": "ai_service_call_succeeded",
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "user_email": user_email,
                }
            },
        ),
        on_failure=lambda status_code, duration_ms, error: log_ai_call_failure(user_email, error),
    )


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
