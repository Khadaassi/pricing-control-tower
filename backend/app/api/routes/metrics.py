from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST

from app.core.metrics import generate_metrics_text

router = APIRouter(tags=["Metrics"])


@router.get(
    "/metrics",
    summary="Métriques Prometheus du backend",
    description=(
        "Expose les métriques applicatives du backend au format Prometheus : "
        "volumétrie des requêtes, codes de réponse HTTP et latence."
    ),
)
def get_metrics() -> Response:
    return Response(
        content=generate_metrics_text(),
        media_type=CONTENT_TYPE_LATEST,
    )
