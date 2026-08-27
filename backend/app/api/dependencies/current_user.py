from datetime import UTC, datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.internal_auth import InvalidServiceToken, decode_service_token
from app.db import get_db
from app.models.user_account import UserAccount

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_business_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> UserAccount:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    try:
        user_email = decode_service_token(credentials.credentials)
    except InvalidServiceToken as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired service token",
        ) from exc

    user = db.scalar(
        select(UserAccount).where(UserAccount.email == user_email)
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Business user not found",
        )

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business user is inactive",
        )

    # Extends the RGPD retention window (see gdpr_retention_service): a user is
    # only ever anonymized after 12 months with no authenticated request at all.
    user.last_active_at = datetime.now(UTC)
    db.commit()

    return user