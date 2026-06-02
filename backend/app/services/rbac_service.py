from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user_account import UserAccount
from app.models.user_role import UserRole


def get_user_permission_codes(
    db: Session,
    user_id: int,
) -> set[str]:
    stmt = (
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
    )

    return set(db.scalars(stmt).all())


def user_has_permission(
    db: Session,
    user_id: int,
    permission_code: str,
) -> bool:
    permissions = get_user_permission_codes(db=db, user_id=user_id)
    return permission_code in permissions


def ensure_user_has_permission(
    db: Session,
    user: UserAccount,
    permission_code: str,
) -> None:
    if not user_has_permission(
        db=db,
        user_id=user.id,
        permission_code=permission_code,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission_code} is required",
        )