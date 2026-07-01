from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from django.http import HttpRequest, HttpResponse

from core.metrics import (
    increment_django_http_requests_total,
    increment_django_http_responses_total,
    observe_django_http_request_duration_seconds,
)

logger = logging.getLogger("pricing_control_tower.frontend")


class StructuredRequestLoggingMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start_time = time.perf_counter()
        user_email = self.get_user_email(request)

        logger.info(
            "Frontend request started",
            extra={
                "extra_fields": {
                    "event": "frontend_request_started",
                    "method": request.method,
                    "path": request.path,
                    "query_string": request.META.get("QUERY_STRING") or "",
                    "user_email": user_email,
                }
            },
        )

        try:
            response = self.get_response(request)

        except Exception:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            logger.exception(
                "Frontend request failed",
                extra={
                    "extra_fields": {
                        "event": "frontend_request_failed",
                        "method": request.method,
                        "path": request.path,
                        "duration_ms": duration_ms,
                        "user_email": user_email,
                    }
                },
            )

            raise

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        log_payload: dict[str, Any] = {
            "event": "frontend_request_completed",
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "user_email": user_email,
        }

        if response.status_code >= 400:
            logger.warning(
                "Frontend request completed with error status",
                extra={"extra_fields": log_payload},
            )
        else:
            logger.info(
                "Frontend request completed",
                extra={"extra_fields": log_payload},
            )

        return response

    @staticmethod
    def get_user_email(request: HttpRequest) -> str | None:
        user = getattr(request, "user", None)

        if user is None:
            return None

        if not getattr(user, "is_authenticated", False):
            return None

        return getattr(user, "email", None) or getattr(user, "username", None)


class PrometheusMetricsMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        method = request.method
        start_time = time.perf_counter()

        response = self.get_response(request)

        duration_seconds = time.perf_counter() - start_time
        resolver_match = getattr(request, "resolver_match", None)
        path = f"/{resolver_match.route}" if resolver_match is not None else request.path

        increment_django_http_requests_total(method, path)
        increment_django_http_responses_total(method, path, str(response.status_code))
        observe_django_http_request_duration_seconds(method, path, duration_seconds)

        return response