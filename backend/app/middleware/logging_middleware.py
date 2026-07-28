from __future__ import annotations

import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.internal_auth import InvalidServiceToken, decode_service_token

logger = logging.getLogger("pricing_control_tower.api")


def _extract_user_email(request: Request) -> str | None:
    authorization = request.headers.get("Authorization")

    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.removeprefix("Bearer ").strip()

    try:
        return decode_service_token(token)
    except InvalidServiceToken:
        return None


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        start_time = time.perf_counter()

        method = request.method
        path = request.url.path
        user_email = _extract_user_email(request)

        request_log = {
            "event": "http_request_started",
            "method": method,
            "path": path,
            "query_params": str(request.query_params),
            "user_email": user_email,
            "client_host": request.client.host if request.client else None,
        }

        logger.info(
            "HTTP request started",
            extra={"extra_fields": request_log},
        )

        try:
            response = await call_next(request)

        except Exception:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            error_log = {
                "event": "http_request_failed",
                "method": method,
                "path": path,
                "duration_ms": duration_ms,
                "user_email": user_email,
                "client_host": request.client.host if request.client else None,
            }

            logger.exception(
                "HTTP request failed",
                extra={"extra_fields": error_log},
            )

            raise

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        response_log = {
            "event": "http_request_completed",
            "method": method,
            "path": path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "user_email": user_email,
            "client_host": request.client.host if request.client else None,
        }

        log_level = logging.ERROR if response.status_code >= 500 else logging.INFO

        logger.log(
            log_level,
            "HTTP request completed",
            extra={"extra_fields": response_log},
        )

        return response