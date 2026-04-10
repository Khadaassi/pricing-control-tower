from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.promotion import Promotion
from app.schemas.promotion import PromotionRead

router = APIRouter(prefix="/promotions", tags=["Promotions"])


@router.get("", response_model=list[PromotionRead])
def list_promotions(db: Session = Depends(get_db)) -> list[Promotion]:
    stmt = select(Promotion).order_by(Promotion.id.asc())
    promotions = db.scalars(stmt).all()
    return list(promotions)