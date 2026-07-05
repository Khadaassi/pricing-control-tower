from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.product_family import ProductFamily
from app.schemas.product import ProductFamilyRead

router = APIRouter(prefix="/product-families", tags=["Reference"])


@router.get("", response_model=list[ProductFamilyRead])
def list_product_families(db: Session = Depends(get_db)):
    stmt = select(ProductFamily).order_by(ProductFamily.name.asc())
    return list(db.scalars(stmt).all())
