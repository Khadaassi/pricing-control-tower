from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from fastapi import APIRouter, Depends

from app.db import get_db
from app.models.product import Product
from app.schemas.product import ProductRead

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db)) -> list[Product]:
    stmt = (
        select(Product)
        .options(selectinload(Product.family))
        .order_by(Product.id.asc())
    )
    products = db.scalars(stmt).all()
    return list(products)
