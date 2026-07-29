from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies.current_user import get_current_business_user
from app.db import get_db
from app.models.promotion import DiscountType, Promotion
from app.models.user_account import UserAccount
from app.schemas.promotion import PromotionCreate, PromotionRead
from app.services.rbac_service import ensure_user_has_permission
from app.services.scope_service import (
    apply_promotion_scope,
    ensure_country_filter_allowed,
    ensure_store_belongs_to_country_scope,
    ensure_store_filter_allowed,
)

router = APIRouter(prefix="/promotions", tags=["Promotions"])


@router.get("")
def list_promotions(
    country_id: int | None = Query(default=None),
    store_id: int | None = Query(default=None),
    active: bool | None = Query(default=None),
    discount_type: DiscountType | None = Query(default=None),
    product_id: int | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int = Query(default=12, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserAccount = Depends(get_current_business_user),
):
    ensure_country_filter_allowed(current_user, country_id)
    ensure_store_filter_allowed(current_user, store_id)
    ensure_store_belongs_to_country_scope(db, current_user, store_id)

    stmt = select(Promotion)
    stmt = apply_promotion_scope(stmt, current_user)

    if country_id is not None:
        stmt = stmt.where(Promotion.country_id == country_id)

    if store_id is not None:
        stmt = stmt.where(Promotion.store_id == store_id)

    if active is not None:
        stmt = stmt.where(Promotion.active == active)

    if discount_type is not None:
        stmt = stmt.where(Promotion.discount_type == discount_type.value)

    if product_id is not None:
        stmt = stmt.where(Promotion.product_id == product_id)

    if date_from is not None:
        stmt = stmt.where(Promotion.start_date >= date_from)

    if date_to is not None:
        stmt = stmt.where(Promotion.start_date <= date_to)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0

    stmt = stmt.order_by(Promotion.id.asc()).limit(limit).offset(offset)

    items = [PromotionRead.model_validate(p).model_dump() for p in db.scalars(stmt).all()]

    return {"items": items, "total": total}


@router.post("", response_model=PromotionRead, status_code=201)
def create_promotion(
    payload: PromotionCreate,
    db: Session = Depends(get_db),
    current_user: UserAccount = Depends(get_current_business_user),
):
    required_permission = (
        "CREATE_STORE_PROMOTION"
        if payload.store_id is not None
        else "CREATE_COUNTRY_PROMOTION"
    )

    ensure_user_has_permission(
        db=db,
        user=current_user,
        permission_code=required_permission,
    )

    ensure_country_filter_allowed(current_user, payload.country_id)
    ensure_store_filter_allowed(current_user, payload.store_id)
    ensure_store_belongs_to_country_scope(db, current_user, payload.store_id)

    promo_data = payload.model_dump()
    promo_data["created_by"] = current_user.id

    promo = Promotion(**promo_data)
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return promo


@router.patch("/{promotion_id}/deactivate", response_model=PromotionRead)
def deactivate_promotion(
    promotion_id: int,
    db: Session = Depends(get_db),
    current_user: UserAccount = Depends(get_current_business_user),
):
    promotion = db.get(Promotion, promotion_id)

    if promotion is None:
        raise HTTPException(status_code=404, detail="Promotion not found")

    ensure_country_filter_allowed(current_user, promotion.country_id)
    ensure_store_filter_allowed(current_user, promotion.store_id)
    ensure_store_belongs_to_country_scope(db, current_user, promotion.store_id)

    required_permission = (
        "STOP_STORE_PROMOTION"
        if promotion.store_id is not None
        else "STOP_COUNTRY_PROMOTION"
    )

    ensure_user_has_permission(
        db=db,
        user=current_user,
        permission_code=required_permission,
    )

    if not promotion.active:
        raise HTTPException(status_code=409, detail="Promotion is already inactive")

    promotion.active = False
    db.commit()
    db.refresh(promotion)
    return promotion