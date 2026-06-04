from __future__ import annotations

import logging
import time
from typing import Any

import requests
from django.conf import settings

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

    return {"X-User-Email": user_email}


def api_get(
    endpoint: str,
    params: dict[str, Any] | None = None,
    user_email: str | None = None,
) -> Any:
    url = build_api_url(endpoint)
    start_time = time.perf_counter()

    try:
        response = requests.get(
            url,
            params=params,
            headers=build_user_headers(user_email),
            timeout=5,
        )
        response.raise_for_status()

        log_api_success(
            method="GET",
            endpoint=endpoint,
            status_code=response.status_code,
            duration_ms=get_duration_ms(start_time),
            user_email=user_email,
        )

        return response.json()

    except requests.exceptions.ConnectionError as exc:
        error_message = "Unable to connect to FastAPI backend."

        log_api_failure(
            method="GET",
            endpoint=endpoint,
            status_code=None,
            duration_ms=get_duration_ms(start_time),
            user_email=user_email,
            error=error_message,
        )

        raise ApiConnectionError(error_message) from exc

    except requests.exceptions.Timeout as exc:
        error_message = "FastAPI backend request timed out."

        log_api_failure(
            method="GET",
            endpoint=endpoint,
            status_code=None,
            duration_ms=get_duration_ms(start_time),
            user_email=user_email,
            error=error_message,
        )

        raise ApiConnectionError(error_message) from exc

    except requests.exceptions.HTTPError as exc:
        error_message = extract_api_error_message(response)

        log_api_failure(
            method="GET",
            endpoint=endpoint,
            status_code=response.status_code,
            duration_ms=get_duration_ms(start_time),
            user_email=user_email,
            error=error_message,
        )

        raise ApiResponseError(error_message) from exc

    except requests.exceptions.JSONDecodeError as exc:
        error_message = "FastAPI backend returned invalid JSON."

        log_api_failure(
            method="GET",
            endpoint=endpoint,
            status_code=response.status_code,
            duration_ms=get_duration_ms(start_time),
            user_email=user_email,
            error=error_message,
        )

        raise ApiResponseError(error_message) from exc


def api_post(
    endpoint: str,
    payload: dict[str, Any] | None = None,
    user_email: str | None = None,
) -> Any:
    url = build_api_url(endpoint)
    start_time = time.perf_counter()

    try:
        response = requests.post(
            url,
            json=payload,
            headers=build_user_headers(user_email),
            timeout=5,
        )
        response.raise_for_status()

        log_api_success(
            method="POST",
            endpoint=endpoint,
            status_code=response.status_code,
            duration_ms=get_duration_ms(start_time),
            user_email=user_email,
        )

        return response.json()

    except requests.exceptions.ConnectionError as exc:
        error_message = "Unable to connect to FastAPI backend."

        log_api_failure(
            method="POST",
            endpoint=endpoint,
            status_code=None,
            duration_ms=get_duration_ms(start_time),
            user_email=user_email,
            error=error_message,
        )

        raise ApiConnectionError(error_message) from exc

    except requests.exceptions.Timeout as exc:
        error_message = "FastAPI backend request timed out."

        log_api_failure(
            method="POST",
            endpoint=endpoint,
            status_code=None,
            duration_ms=get_duration_ms(start_time),
            user_email=user_email,
            error=error_message,
        )

        raise ApiConnectionError(error_message) from exc

    except requests.exceptions.HTTPError as exc:
        error_message = extract_api_error_message(response)

        log_api_failure(
            method="POST",
            endpoint=endpoint,
            status_code=response.status_code,
            duration_ms=get_duration_ms(start_time),
            user_email=user_email,
            error=error_message,
        )

        raise ApiResponseError(error_message) from exc

    except requests.exceptions.JSONDecodeError as exc:
        error_message = "FastAPI backend returned invalid JSON."

        log_api_failure(
            method="POST",
            endpoint=endpoint,
            status_code=response.status_code,
            duration_ms=get_duration_ms(start_time),
            user_email=user_email,
            error=error_message,
        )

        raise ApiResponseError(error_message) from exc


def api_patch(
    endpoint: str,
    payload: dict[str, Any] | None = None,
    user_email: str | None = None,
) -> Any:
    url = build_api_url(endpoint)
    start_time = time.perf_counter()

    try:
        response = requests.patch(
            url,
            json=payload,
            headers=build_user_headers(user_email),
            timeout=5,
        )
        response.raise_for_status()

        log_api_success(
            method="PATCH",
            endpoint=endpoint,
            status_code=response.status_code,
            duration_ms=get_duration_ms(start_time),
            user_email=user_email,
        )

        return response.json()

    except requests.exceptions.ConnectionError as exc:
        error_message = "Unable to connect to FastAPI backend."

        log_api_failure(
            method="PATCH",
            endpoint=endpoint,
            status_code=None,
            duration_ms=get_duration_ms(start_time),
            user_email=user_email,
            error=error_message,
        )

        raise ApiConnectionError(error_message) from exc

    except requests.exceptions.Timeout as exc:
        error_message = "FastAPI backend request timed out."

        log_api_failure(
            method="PATCH",
            endpoint=endpoint,
            status_code=None,
            duration_ms=get_duration_ms(start_time),
            user_email=user_email,
            error=error_message,
        )

        raise ApiConnectionError(error_message) from exc

    except requests.exceptions.HTTPError as exc:
        error_message = extract_api_error_message(response)

        log_api_failure(
            method="PATCH",
            endpoint=endpoint,
            status_code=response.status_code,
            duration_ms=get_duration_ms(start_time),
            user_email=user_email,
            error=error_message,
        )

        raise ApiResponseError(error_message) from exc

    except requests.exceptions.JSONDecodeError as exc:
        error_message = "FastAPI backend returned invalid JSON."

        log_api_failure(
            method="PATCH",
            endpoint=endpoint,
            status_code=response.status_code,
            duration_ms=get_duration_ms(start_time),
            user_email=user_email,
            error=error_message,
        )

        raise ApiResponseError(error_message) from exc


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


def get_duration_ms(start_time: float) -> float:
    return round((time.perf_counter() - start_time) * 1000, 2)


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