from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST

from app.core.metrics import generate_metrics_text

router = APIRouter(tags=["Metrics"])


@router.get(
    "/metrics",
    summary="Métriques Prometheus du chatbot",
    description=(
        "Expose les métriques applicatives du chatbot au format Prometheus : "
        "volumétrie des requêtes, statuts de réponse, erreurs techniques, outils "
        "métier utilisés et latence de réponse."
    ),
)
def get_metrics() -> Response:
    return Response(
        content=generate_metrics_text(),
        media_type=CONTENT_TYPE_LATEST,
    )
