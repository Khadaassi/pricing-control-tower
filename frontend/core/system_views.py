from datetime import UTC, datetime

from django.http import HttpRequest, HttpResponse, JsonResponse
from prometheus_client import CONTENT_TYPE_LATEST

from core.metrics import generate_metrics_text


def health_view(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        {
            "status": "ok",
            "service": "pricing-control-tower-frontend",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


def metrics_view(request: HttpRequest) -> HttpResponse:
    return HttpResponse(generate_metrics_text(), content_type=CONTENT_TYPE_LATEST)
