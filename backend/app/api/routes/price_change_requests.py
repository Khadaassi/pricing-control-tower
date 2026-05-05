from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.price_change_request import (
    PriceChangeRequestCreate,
    PriceChangeRequestRead,
)
from app.services.price_change_request_service import (
    create_price_change_request,
    list_price_change_requests,
)

router = APIRouter(
    prefix="/price-change-requests",
    tags=["Price Change Requests"],
)


@router.post(
    "",
    response_model=PriceChangeRequestRead,
    status_code=status.HTTP_201_CREATED,
)
def create_price_change_request_endpoint(
    payload: PriceChangeRequestCreate,
    db: Session = Depends(get_db),
) -> PriceChangeRequestRead:
    return create_price_change_request(db=db, payload=payload)

@router.get(
    "",
    response_model=list[PriceChangeRequestRead],
)
def get_price_change_requests_endpoint(
    status: str | None = None,
    product_id: int | None = Query(default=None, gt=0),
    country_id: int | None = Query(default=None, gt=0),
    store_id: int | None = Query(default=None, gt=0),
    requested_by_user_id: int | None = Query(default=None, gt=0),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[PriceChangeRequestRead]:
    return list_price_change_requests(
        db=db,
        status=status,
        product_id=product_id,
        country_id=country_id,
        store_id=store_id,
        requested_by_user_id=requested_by_user_id,
        limit=limit,
        offset=offset,
    )
