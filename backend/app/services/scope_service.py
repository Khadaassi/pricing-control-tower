from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.price import Price
from app.models.promotion import Promotion
from app.models.store import Store
from app.models.user_account import UserAccount


def is_global_user(user: UserAccount) -> bool:
    return user.country_id is None and user.store_id is None


def is_country_user(user: UserAccount) -> bool:
    return user.country_id is not None and user.store_id is None


def is_store_user(user: UserAccount) -> bool:
    return user.country_id is not None and user.store_id is not None


def get_country_store_ids(db: Session, country_id: int) -> list[int]:
    return list(
        db.scalars(
            select(Store.id).where(Store.country_id == country_id)
        ).all()
    )


def ensure_country_filter_allowed(
    user: UserAccount,
    requested_country_id: int | None,
) -> None:
    if is_global_user(user):
        return

    if requested_country_id is not None and requested_country_id != user.country_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Country filter is outside the user's scope",
        )


def ensure_store_filter_allowed(
    user: UserAccount,
    requested_store_id: int | None,
) -> None:
    if is_global_user(user):
        return

    if requested_store_id is None:
        return

    if is_store_user(user) and requested_store_id != user.store_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Store filter is outside the user's scope",
        )


def ensure_store_belongs_to_country_scope(
    db: Session,
    user: UserAccount,
    requested_store_id: int | None,
) -> None:
    if is_global_user(user) or requested_store_id is None:
        return

    store = db.get(Store, requested_store_id)

    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found",
        )

    if store.country_id != user.country_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Store filter is outside the user's country scope",
        )


def apply_price_scope(
    stmt: Select,
    user: UserAccount,
) -> Select:
    if is_global_user(user):
        return stmt

    if is_store_user(user):
        return stmt.where(
            Price.country_id == user.country_id,
            (
                (Price.store_id == user.store_id)
                | (Price.store_id.is_(None))
            ),
        )

    return stmt.where(Price.country_id == user.country_id)


def apply_promotion_scope(
    stmt: Select,
    user: UserAccount,
) -> Select:
    if is_global_user(user):
        return stmt

    if is_store_user(user):
        return stmt.where(
            Promotion.country_id == user.country_id,
            (
                (Promotion.store_id == user.store_id)
                | (Promotion.store_id.is_(None))
            ),
        )

    return stmt.where(Promotion.country_id == user.country_id)


def resolve_allowed_store_ids_for_analytics(
    db: Session,
    user: UserAccount,
) -> list[int] | None:
    if is_global_user(user):
        return None

    if is_store_user(user):
        return [user.store_id]

    return get_country_store_ids(db=db, country_id=user.country_id)