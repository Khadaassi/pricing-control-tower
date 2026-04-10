from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models.price import Price
from app.schemas.price import PriceRead

router = APIRouter(prefix="/prices", tags=["Prices"])


@router.get("", response_model=list[PriceRead])
def list_prices(db: Session = Depends(get_db)) -> list[PriceRead]:
    stmt = (
        select(Price)
        .options(selectinload(Price.product))
        .order_by(Price.id.asc())
    )

    prices = db.scalars(stmt).all()

    return [
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
        )
        for p in prices
    ]
