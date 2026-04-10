from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models.product import Product
from app.schemas.product import ProductRead

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=list[ProductRead])
def list_products(
    active: bool | None = Query(default=None),
    product_family_id: int | None = Query(default=None),
    code: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(Product).options(selectinload(Product.family))

    if active is not None:
        stmt = stmt.where(Product.active == active)

    if product_family_id is not None:
        stmt = stmt.where(Product.product_family_id == product_family_id)

    if code is not None:
        stmt = stmt.where(Product.code == code)

    stmt = stmt.order_by(Product.id.asc())

    return list(db.scalars(stmt).all())