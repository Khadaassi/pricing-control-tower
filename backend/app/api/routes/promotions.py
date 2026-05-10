from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.promotion import DiscountType, Promotion
from app.schemas.promotion import PromotionRead

router = APIRouter(prefix="/promotions", tags=["Promotions"])


@router.get("", response_model=list[PromotionRead])
def list_promotions(
    country_id: int | None = Query(default=None),
    store_id: int | None = Query(default=None),
    active: bool | None = Query(default=None),
    discount_type: DiscountType | None = Query(default=None),
    product_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(Promotion)

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

    stmt = stmt.order_by(Promotion.id.asc())

    return list(db.scalars(stmt).all())


@router.patch("/{promotion_id}/deactivate", response_model=PromotionRead)
def deactivate_promotion(promotion_id: int, db: Session = Depends(get_db)):
    promotion = db.get(Promotion, promotion_id)
    if promotion is None:
        raise HTTPException(status_code=404, detail="Promotion not found")
    if not promotion.active:
        raise HTTPException(status_code=409, detail="Promotion is already inactive")
    promotion.active = False
    db.commit()
    db.refresh(promotion)
    return promotion