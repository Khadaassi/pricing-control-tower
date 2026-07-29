"""Shared low-level HTTP request helper for the frontend's outbound API clients.

Both services/api_client.py (→ FastAPI backend) and core/services/ai_chatbot_client.py
(→ ai_service) hit a JSON HTTP API and need the same connection/timeout/HTTP-error/bad-JSON
handling. Each caller supplies its own exception classes and log callbacks so the two stay
independently catchable (ChatbotView catches AiChatbot*Error, other views catch Api*Error) and
keep their existing structured-log shape.
"""
from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import requests


def do_request(
    method: str,
    url: str,
    *,
    service_label: str,
    connection_error_cls: type[Exception],
    response_error_cls: type[Exception],
    on_success: Callable[[int, float], None] | None = None,
    on_failure: Callable[[int | None, float, str], None] | None = None,
    error_message_from_response: Callable[[requests.Response], str] | None = None,
    **request_kwargs: Any,
) -> Any:
    """Perform a JSON HTTP request, mapping requests' exceptions onto the caller's own
    exception hierarchy. Returns the parsed JSON body on success."""
    start_time = time.perf_counter()

    try:
        response = requests.request(method, url, **request_kwargs)
        response.raise_for_status()
        data = response.json()

    except requests.exceptions.ConnectionError as exc:
        message = f"Unable to connect to {service_label}."
        _report_failure(on_failure, None, start_time, message)
        raise connection_error_cls(message) from exc

    except requests.exceptions.Timeout as exc:
        message = f"{service_label} request timed out."
        _report_failure(on_failure, None, start_time, message)
        raise connection_error_cls(message) from exc

    except requests.exceptions.HTTPError as exc:
        message = (
            error_message_from_response(response)
            if error_message_from_response
            else f"{service_label} returned an error: {response.status_code}"
        )
        _report_failure(on_failure, response.status_code, start_time, message)
        raise response_error_cls(message) from exc

    except requests.exceptions.JSONDecodeError as exc:
        message = f"{service_label} returned invalid JSON."
        _report_failure(on_failure, response.status_code, start_time, message)
        raise response_error_cls(message) from exc

    if on_success:
        on_success(response.status_code, _elapsed_ms(start_time))

    return data


def _report_failure(
    on_failure: Callable[[int | None, float, str], None] | None,
    status_code: int | None,
    start_time: float,
    message: str,
) -> None:
    if on_failure:
        on_failure(status_code, _elapsed_ms(start_time), message)


def _elapsed_ms(start_time: float) -> float:
    return round((time.perf_counter() - start_time) * 1000, 2)
