from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.current_user import get_current_business_user
from app.db import get_db
from app.models.user_account import UserAccount
from app.services.price_history_service import list_price_history
from app.services.scope_service import (
    ensure_country_filter_allowed,
    ensure_store_belongs_to_country_scope,
    ensure_store_filter_allowed,
)

router = APIRouter(
    prefix="/price-history",
    tags=["Price History"],
)


@router.get("")
def get_price_history_endpoint(
    price_change_request_id: int | None = Query(default=None, gt=0),
    product_id: int | None = Query(default=None, gt=0),
    country_id: int | None = Query(default=None, gt=0),
    store_id: int | None = Query(default=None, gt=0),
    applied_by_user_id: int | None = Query(default=None, gt=0),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserAccount = Depends(get_current_business_user),
) -> dict:
    ensure_country_filter_allowed(current_user, country_id)
    ensure_store_filter_allowed(current_user, store_id)
    ensure_store_belongs_to_country_scope(db, current_user, store_id)

    items, total = list_price_history(
        db=db,
        user=current_user,
        price_change_request_id=price_change_request_id,
        product_id=product_id,
        country_id=country_id,
        store_id=store_id,
        applied_by_user_id=applied_by_user_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return {"items": items, "total": total}