from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings

from services.http import do_request
from services.internal_auth import issue_service_token

logger = logging.getLogger("pricing_control_tower.frontend.api_client")


class ApiClientError(Exception):
    """Base exception for frontend API client errors."""


class ApiConnectionError(ApiClientError):
    """Raised when the FastAPI backend cannot be reached."""


class ApiResponseError(ApiClientError):
    """Raised when the FastAPI backend returns an unexpected response."""


def build_api_url(endpoint: str) -> str:
    base_url = settings.FASTAPI_BASE_URL.rstrip("/")
    endpoint_path = endpoint.lstrip("/")
    return f"{base_url}/{endpoint_path}"


def build_user_headers(user_email: str | None = None) -> dict[str, str]:
    if not user_email:
        return {}

    return {"Authorization": f"Bearer {issue_service_token(user_email)}"}


def _call_backend(
    method: str,
    endpoint: str,
    *,
    params: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    user_email: str | None = None,
) -> Any:
    url = build_api_url(endpoint)

    return do_request(
        method,
        url,
        service_label="FastAPI backend",
        connection_error_cls=ApiConnectionError,
        response_error_cls=ApiResponseError,
        error_message_from_response=extract_api_error_message,
        params=params,
        json=payload,
        headers=build_user_headers(user_email),
        timeout=5,
        on_success=lambda status_code, duration_ms: log_api_success(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration_ms=duration_ms,
            user_email=user_email,
        ),
        on_failure=lambda status_code, duration_ms, error: log_api_failure(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration_ms=duration_ms,
            user_email=user_email,
            error=error,
        ),
    )


def api_get(
    endpoint: str,
    params: dict[str, Any] | None = None,
    user_email: str | None = None,
) -> Any:
    return _call_backend("GET", endpoint, params=params, user_email=user_email)


def api_post(
    endpoint: str,
    payload: dict[str, Any] | None = None,
    user_email: str | None = None,
) -> Any:
    return _call_backend("POST", endpoint, payload=payload, user_email=user_email)


def api_patch(
    endpoint: str,
    payload: dict[str, Any] | None = None,
    user_email: str | None = None,
) -> Any:
    return _call_backend("PATCH", endpoint, payload=payload, user_email=user_email)


def extract_api_error_message(response: requests.Response) -> str:
    try:
        error_payload = response.json()
    except requests.exceptions.JSONDecodeError:
        return f"FastAPI backend returned an error: {response.status_code}"

    detail = error_payload.get("detail")

    if isinstance(detail, str):
        return detail

    if isinstance(detail, list):
        messages = []

        for error in detail:
            location = error.get("loc", [])
            field_name = location[-1] if location else "field"
            message = error.get("msg", "Invalid value")
            messages.append(f"{field_name}: {message}")

        return " | ".join(messages)

    return f"FastAPI backend returned an error: {response.status_code}"


def log_api_success(
    method: str,
    endpoint: str,
    status_code: int,
    duration_ms: float,
    user_email: str | None,
) -> None:
    logger.info(
        "FastAPI call succeeded",
        extra={
            "extra_fields": {
                "event": "api_call_succeeded",
                "method": method,
                "endpoint": endpoint,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "user_email": user_email,
            }
        },
    )


def log_api_failure(
    method: str,
    endpoint: str,
    status_code: int | None,
    duration_ms: float,
    user_email: str | None,
    error: str,
) -> None:
    logger.warning(
        "FastAPI call failed",
        extra={
            "extra_fields": {
                "event": "api_call_failed",
                "method": method,
                "endpoint": endpoint,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "user_email": user_email,
                "error": error,
            }
        },
    )
