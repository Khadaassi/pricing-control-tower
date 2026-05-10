from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.anomaly import BusinessAnomalyRead
from app.services.anomaly_service import get_business_anomalies

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get(
    "",
    response_model=list[BusinessAnomalyRead],
    summary="Liste des anomalies tarifaires et commerciales",
    description=(
        "Retourne les anomalies détectées statistiquement à partir du modèle analytique "
        "(pct_analytics). "
        "Deux règles sont appliquées par famille produit : "
        "(1) LOW_PROMOTION_REVENUE — CA d'une promotion inférieur à moyenne - "
        "1×écart-type de sa famille ; "
        "(2) ABNORMAL_DISCOUNT_RATE — taux de remise supérieur à moyenne + "
        "2×écart-type de sa famille."
    ),
)
def list_business_anomalies(
    db: Annotated[Session, Depends(get_db)],
    promotion_id: int | None = Query(
        default=None, description="Filtrer par identifiant de promotion"
    ),
    product_id: int | None = Query(
        default=None, description="Filtrer par identifiant produit"
    ),
    store_id: int | None = Query(
        default=None, description="Filtrer par identifiant magasin"
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Nombre maximum d'anomalies à retourner",
    ),
) -> list[BusinessAnomalyRead]:
    return get_business_anomalies(
        db=db,
        promotion_id=promotion_id,
        product_id=product_id,
        store_id=store_id,
        limit=limit,
    )
