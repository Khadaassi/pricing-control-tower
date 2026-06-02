from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.current_user import get_current_business_user
from app.db import get_db
from app.models.user_account import UserAccount
from app.schemas.current_user import CurrentUserRead
from app.services.rbac_service import (
    get_user_permission_codes,
    get_user_role_codes,
)

router = APIRouter(prefix="/me", tags=["Current User"])


@router.get("", response_model=CurrentUserRead)
def get_me(
    db: Session = Depends(get_db),
    current_user: UserAccount = Depends(get_current_business_user),
) -> CurrentUserRead:
    return CurrentUserRead(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        active=current_user.active,
        country_id=current_user.country_id,
        store_id=current_user.store_id,
        roles=sorted(get_user_role_codes(db=db, user_id=current_user.id)),
        permissions=sorted(get_user_permission_codes(db=db, user_id=current_user.id)),
    )