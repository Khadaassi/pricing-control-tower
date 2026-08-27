from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.current_user import get_current_business_user
from app.db import get_db
from app.models.product_family import ProductFamily
from app.models.user_account import UserAccount
from app.schemas.product import ProductFamilyRead

router = APIRouter(prefix="/product-families", tags=["Reference"])


@router.get("", response_model=list[ProductFamilyRead])
def list_product_families(
    db: Session = Depends(get_db),
    current_user: UserAccount = Depends(get_current_business_user),
):
    stmt = select(ProductFamily).order_by(ProductFamily.name.asc())
    return list(db.scalars(stmt).all())
