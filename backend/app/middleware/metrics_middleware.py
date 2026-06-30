from __future__ import annotations

import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.metrics import (
    increment_http_requests_total,
    increment_http_responses_total,
    observe_http_request_duration_seconds,
)


def _resolve_path_template(request: Request) -> str:
    route = request.scope.get("route")
    return route.path if route is not None else request.url.path


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        method = request.method
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_seconds = time.perf_counter() - start_time
            path = _resolve_path_template(request)
            increment_http_requests_total(method, path)
            increment_http_responses_total(method, path, "500")
            observe_http_request_duration_seconds(method, path, duration_seconds)
            raise

        duration_seconds = time.perf_counter() - start_time
        path = _resolve_path_template(request)

        increment_http_requests_total(method, path)
        increment_http_responses_total(method, path, str(response.status_code))
        observe_http_request_duration_seconds(method, path, duration_seconds)

        return response
