from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies.current_user import get_current_business_user
from app.db import get_db
from app.models.price import Price
from app.models.user_account import UserAccount
from app.schemas.price import PriceRead
from app.services.scope_service import (
    apply_price_scope,
    ensure_country_filter_allowed,
    ensure_store_belongs_to_country_scope,
    ensure_store_filter_allowed,
)

router = APIRouter(prefix="/prices", tags=["Prices"])


@router.get("")
def list_prices(
    product_id: int | None = Query(default=None),
    country_id: int | None = Query(default=None),
    store_id: int | None = Query(default=None),
    price_scope: str | None = Query(default=None),
    price_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserAccount = Depends(get_current_business_user),
):
    ensure_country_filter_allowed(current_user, country_id)
    ensure_store_filter_allowed(current_user, store_id)
    ensure_store_belongs_to_country_scope(db, current_user, store_id)

    stmt = select(Price).options(selectinload(Price.product))
    stmt = apply_price_scope(stmt, current_user)

    if product_id is not None:
        stmt = stmt.where(Price.product_id == product_id)

    if country_id is not None:
        stmt = stmt.where(Price.country_id == country_id)

    if store_id is not None:
        stmt = stmt.where(Price.store_id == store_id)

    if price_scope is not None:
        stmt = stmt.where(Price.price_scope == price_scope)

    if price_type is not None:
        stmt = stmt.where(Price.price_type == price_type)

    if status is not None:
        stmt = stmt.where(Price.status == status)

    if date_from is not None:
        stmt = stmt.where(Price.effective_from >= date_from)

    if date_to is not None:
        stmt = stmt.where(Price.effective_from <= date_to)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0

    stmt = stmt.order_by(Price.id.asc()).limit(limit).offset(offset)

    prices = db.scalars(stmt).all()

    items = [
        PriceRead(
            id=p.id,
            product_id=p.product_id,
            product_code=p.product.code,
            product_name=p.product.name,
            price_scope=p.price_scope,
            country_id=p.country_id,
            store_id=p.store_id,
            price_type=p.price_type,
            amount=p.amount,
            currency_code=p.currency_code,
            effective_from=p.effective_from,
            effective_to=p.effective_to,
            status=p.status,
            promotion_id=p.promotion_id,
        ).model_dump()
        for p in prices
    ]

    return {"items": items, "total": total}