from typing import Any

import requests
from django.conf import settings


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


def api_get(endpoint: str, params: dict[str, Any] | None = None) -> Any:
    url = build_api_url(endpoint)

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError as exc:
        raise ApiConnectionError("Unable to connect to FastAPI backend.") from exc
    except requests.exceptions.Timeout as exc:
        raise ApiConnectionError("FastAPI backend request timed out.") from exc
    except requests.exceptions.HTTPError as exc:
        raise ApiResponseError(
            f"FastAPI backend returned an error: {response.status_code}"
        ) from exc
    except requests.exceptions.JSONDecodeError as exc:
        raise ApiResponseError("FastAPI backend returned invalid JSON.") from exc


def api_post(endpoint: str, payload: dict[str, Any] | None = None) -> Any:
    url = build_api_url(endpoint)

    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError as exc:
        raise ApiConnectionError("Unable to connect to FastAPI backend.") from exc
    except requests.exceptions.Timeout as exc:
        raise ApiConnectionError("FastAPI backend request timed out.") from exc
    except requests.exceptions.HTTPError as exc:
        raise ApiResponseError(extract_api_error_message(response)) from exc
    except requests.exceptions.JSONDecodeError as exc:
        raise ApiResponseError("FastAPI backend returned invalid JSON.") from exc
    
def api_patch(endpoint: str, payload: dict[str, Any] | None = None) -> Any:
    url = build_api_url(endpoint)

    try:
        response = requests.patch(url, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError as exc:
        raise ApiConnectionError("Unable to connect to FastAPI backend.") from exc
    except requests.exceptions.Timeout as exc:
        raise ApiConnectionError("FastAPI backend request timed out.") from exc
    except requests.exceptions.HTTPError as exc:
        raise ApiResponseError(extract_api_error_message(response)) from exc
    except requests.exceptions.JSONDecodeError as exc:
        raise ApiResponseError("FastAPI backend returned invalid JSON.") from exc


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