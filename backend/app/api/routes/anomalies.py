from decimal import Decimal
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
    summary="List MVP business anomalies",
    description=(
        "Return simple rule-based business anomalies from the analytical sales model. "
        "The MVP rule detects promotions with revenue below a configured threshold."
    ),
)
def list_business_anomalies(
    db: Annotated[Session, Depends(get_db)],
    min_revenue: Decimal = Query(
        default=Decimal("500.00"),
        ge=Decimal("0.00"),
        description="Minimum promotion revenue threshold used to detect anomalies",
    ),
    promotion_id: int | None = Query(default=None, description="Filter by promotion ID"),
    product_id: int | None = Query(default=None, description="Filter by product ID"),
    store_id: int | None = Query(default=None, description="Filter by store ID"),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of anomalies to return",
    ),
) -> list[BusinessAnomalyRead]:
    return get_business_anomalies(
        db=db,
        min_revenue=min_revenue,
        promotion_id=promotion_id,
        product_id=product_id,
        store_id=store_id,
        limit=limit,
    )