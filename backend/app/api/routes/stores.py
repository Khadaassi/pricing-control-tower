from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.store import Store
from app.schemas.reference import StoreRead

router = APIRouter(prefix="/stores", tags=["Reference"])


@router.get("", response_model=list[StoreRead])
def list_stores(
    country_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(Store).order_by(Store.name.asc())
    if country_id is not None:
        stmt = stmt.where(Store.country_id == country_id)
    return list(db.scalars(stmt).all())
