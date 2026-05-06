from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.price_history import PriceHistoryRead
from app.services.price_history_service import list_price_history

router = APIRouter(
    prefix="/price-history",
    tags=["Price History"],
)


@router.get(
    "",
    response_model=list[PriceHistoryRead],
)
def get_price_history_endpoint(
    price_change_request_id: int | None = Query(default=None, gt=0),
    product_id: int | None = Query(default=None, gt=0),
    country_id: int | None = Query(default=None, gt=0),
    store_id: int | None = Query(default=None, gt=0),
    applied_by_user_id: int | None = Query(default=None, gt=0),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[PriceHistoryRead]:
    return list_price_history(
        db=db,
        price_change_request_id=price_change_request_id,
        product_id=product_id,
        country_id=country_id,
        store_id=store_id,
        applied_by_user_id=applied_by_user_id,
        limit=limit,
        offset=offset,
    )