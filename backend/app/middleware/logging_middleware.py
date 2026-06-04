from __future__ import annotations

import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("pricing_control_tower.api")


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        start_time = time.perf_counter()

        method = request.method
        path = request.url.path
        user_email = request.headers.get("X-User-Email")

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