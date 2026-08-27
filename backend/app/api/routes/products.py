from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies.current_user import get_current_business_user
from app.db import get_db
from app.models.product import Product
from app.models.user_account import UserAccount
from app.schemas.product import ProductRead

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("")
def list_products(
    active: bool | None = Query(default=None),
    product_family_id: int | None = Query(default=None),
    code: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserAccount = Depends(get_current_business_user),
):
    stmt = select(Product).options(
        selectinload(Product.family),
        selectinload(Product.images),
    )

    if active is not None:
        stmt = stmt.where(Product.active == active)

    if product_family_id is not None:
        stmt = stmt.where(Product.product_family_id == product_family_id)

    if code is not None:
        stmt = stmt.where(Product.code == code)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0

    stmt = stmt.order_by(Product.id.asc()).limit(limit).offset(offset)

    items = [ProductRead.model_validate(p).model_dump() for p in db.scalars(stmt).all()]

    return {"items": items, "total": total}