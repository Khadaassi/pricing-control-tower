import threading
from typing import Any

from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest

SERVICE_NAME = "backend"

_lock = threading.Lock()


def _build_metrics(registry: CollectorRegistry) -> dict[str, Any]:
    return {
        "requests": Counter(
            "http_requests_total",
            "Total number of HTTP requests received",
            ["method", "path"],
            registry=registry,
        ),
        "responses": Counter(
            "http_responses_total",
            "Total number of HTTP responses by status code",
            ["method", "path", "status_code"],
            registry=registry,
        ),
        "duration": Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "path"],
            registry=registry,
        ),
    }


_registry = CollectorRegistry()
_metrics = _build_metrics(_registry)


def increment_http_requests_total(method: str, path: str) -> None:
    with _lock:
        _metrics["requests"].labels(method=method, path=path).inc()


def increment_http_responses_total(method: str, path: str, status_code: str) -> None:
    with _lock:
        _metrics["responses"].labels(method=method, path=path, status_code=status_code).inc()


def observe_http_request_duration_seconds(method: str, path: str, duration_seconds: float) -> None:
    with _lock:
        _metrics["duration"].labels(method=method, path=path).observe(duration_seconds)


def generate_metrics_text() -> bytes:
    with _lock:
        return generate_latest(_registry)
