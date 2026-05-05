from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.price_change_request import (
    PriceChangeRequestCreate,
    PriceChangeRequestRead,
)
from app.services.price_change_request_service import create_price_change_request

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