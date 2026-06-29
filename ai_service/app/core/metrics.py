import threading
from typing import Any

from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest

SERVICE_NAME = "ai_service"

_lock = threading.Lock()


def _build_metrics(registry: CollectorRegistry) -> dict[str, Any]:
    return {
        "requests": Counter(
            "ai_chat_requests_total",
            "Total number of chat requests received",
            registry=registry,
        ),
        "responses": Counter(
            "ai_chat_responses_total",
            "Total number of chat responses by status",
            ["status"],
            registry=registry,
        ),
        "errors": Counter(
            "ai_chat_errors_total",
            "Total number of chat errors by error type",
            ["error_type"],
            registry=registry,
        ),
        "tool_usage": Counter(
            "ai_chat_tool_usage_total",
            "Total number of times each business tool was used",
            ["tool_name"],
            registry=registry,
        ),
        "latency": Histogram(
            "ai_chat_response_latency_seconds",
            "Chat response latency in seconds",
            registry=registry,
        ),
    }


_registry = CollectorRegistry()
_metrics = _build_metrics(_registry)


def increment_chat_requests_total() -> None:
    with _lock:
        _metrics["requests"].inc()


def increment_chat_responses_total(status: str) -> None:
    with _lock:
        _metrics["responses"].labels(status=status).inc()


def increment_chat_errors_total(error_type: str) -> None:
    with _lock:
        _metrics["errors"].labels(error_type=error_type).inc()


def increment_chat_tool_usage_total(tool_name: str) -> None:
    with _lock:
        _metrics["tool_usage"].labels(tool_name=tool_name).inc()


def observe_chat_response_latency_seconds(latency_seconds: float) -> None:
    with _lock:
        _metrics["latency"].observe(latency_seconds)


def generate_metrics_text() -> bytes:
    with _lock:
        return generate_latest(_registry)


def get_metric_value(metric_name: str, labels: dict[str, str] | None = None) -> float | None:
    with _lock:
        return _registry.get_sample_value(metric_name, labels or {})


def reset_metrics() -> None:
    global _registry, _metrics

    with _lock:
        _registry = CollectorRegistry()
        _metrics = _build_metrics(_registry)
