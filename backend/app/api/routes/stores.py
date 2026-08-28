from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.current_user import get_current_business_user
from app.db import get_db
from app.models.store import Store
from app.models.user_account import UserAccount
from app.schemas.reference import StoreRead

router = APIRouter(prefix="/stores", tags=["Reference"])


@router.get("", response_model=list[StoreRead])
def list_stores(
    country_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserAccount = Depends(get_current_business_user),
):
    stmt = select(Store).order_by(Store.name.asc())
    if country_id is not None:
        stmt = stmt.where(Store.country_id == country_id)
    return list(db.scalars(stmt).all())
