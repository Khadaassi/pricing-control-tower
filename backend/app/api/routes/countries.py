from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.current_user import get_current_business_user
from app.db import get_db
from app.models.country import Country
from app.models.user_account import UserAccount
from app.schemas.reference import CountryRead

router = APIRouter(prefix="/countries", tags=["Reference"])


@router.get("", response_model=list[CountryRead])
def list_countries(
    db: Session = Depends(get_db),
    current_user: UserAccount = Depends(get_current_business_user),
):
    stmt = select(Country).order_by(Country.name.asc())
    return list(db.scalars(stmt).all())
