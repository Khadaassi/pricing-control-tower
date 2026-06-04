from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.current_user import get_current_business_user
from app.db import get_db
from app.models.user_account import UserAccount
from app.schemas.anomaly import BusinessAnomalyRead
from app.services.anomaly_service import get_business_anomalies
from app.services.scope_service import (
    ensure_store_belongs_to_country_scope,
    ensure_store_filter_allowed,
    resolve_allowed_store_ids_for_analytics,
)

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get(
    "",
    summary="List pricing and commercial anomalies",
    description=(
        "Returns pricing anomalies detected by four business rules. "
        "(1) UNDERPERFORMING_PROMO — promotion daily revenue below pre-promotion baseline by more than 10 %; "
        "(2) INEFFECTIVE_DISCOUNT — effective discount ≥ 20 % with no volume uplift; "
        "(3) PRICE_ABOVE_REFERENCE — store price exceeds the national reference price; "
        "(4) INTER_STORE_PRICE_GAP — abnormal deviation between a store price "
        "and the national store average for the same product."
    ),
)
def list_business_anomalies(
    db: Annotated[Session, Depends(get_db)],
    promotion_id: int | None = Query(
        default=None, description="Filter by promotion ID"
    ),
    product_id: int | None = Query(
        default=None, description="Filter by product ID"
    ),
    store_id: int | None = Query(
        default=None, description="Filter by store ID"
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=200,
        description="Maximum number of anomalies to return",
    ),
    offset: int = Query(default=0, ge=0),
    current_user: UserAccount = Depends(get_current_business_user),
) -> dict:
    ensure_store_filter_allowed(current_user, store_id)
    ensure_store_belongs_to_country_scope(db, current_user, store_id)

    allowed_store_ids = resolve_allowed_store_ids_for_analytics(
        db=db,
        user=current_user,
    )

    items, total = get_business_anomalies(
        db=db,
        promotion_id=promotion_id,
        product_id=product_id,
        store_id=store_id,
        allowed_store_ids=allowed_store_ids,
        limit=limit,
        offset=offset,
    )
    return {"items": [item.model_dump() for item in items], "total": total}
