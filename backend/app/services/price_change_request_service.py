from __future__ import annotations

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.price import Price
from app.models.price_change_request import PriceChangeRequest
from app.models.product import Product
from app.models.store import Store
from app.models.country import Country
from app.models.user_account import UserAccount
from app.schemas.price_change_request import PriceChangeRequestCreate


def create_price_change_request(
    db: Session,
    payload: PriceChangeRequestCreate,
) -> PriceChangeRequest:
    product = db.scalar(
        select(Product).where(Product.id == payload.product_id)
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    country = db.scalar(
        select(Country).where(Country.id == payload.country_id)
    )
    if country is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Country not found",
        )

    requester = db.scalar(
        select(UserAccount).where(UserAccount.id == payload.requested_by_user_id)
    )
    if requester is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requesting user not found",
        )

    if payload.store_id is not None:
        store = db.scalar(
            select(Store).where(Store.id == payload.store_id)
        )
        if store is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found",
            )

        if store.country_id != payload.country_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Store does not belong to selected country",
            )

    current_price = get_current_applicable_standard_price(
        db=db,
        product_id=payload.product_id,
        country_id=payload.country_id,
        store_id=payload.store_id,
    )

    if current_price is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Current applicable standard price not found",
        )

    price_change_request = PriceChangeRequest(
        product_id=payload.product_id,
        country_id=payload.country_id,
        store_id=payload.store_id,
        current_price_id=current_price.id,
        old_price_amount=current_price.amount,
        requested_price_amount=payload.requested_price_amount,
        status="PENDING",
        justification=payload.justification,
        requested_effective_date=payload.requested_effective_date,
        requested_by_user_id=payload.requested_by_user_id,
    )

    db.add(price_change_request)
    db.flush()

    audit_log = AuditLog(
        price_change_request_id=price_change_request.id,
        action_type="REQUEST_CREATED",
        performed_by_user_id=payload.requested_by_user_id,
        description=(
            "Price change request created with status PENDING. "
            f"Product ID: {payload.product_id}, "
            f"Country ID: {payload.country_id}, "
            f"Store ID: {payload.store_id}, "
            f"Current price ID: {current_price.id}, "
            f"Old price amount: {current_price.amount}, "
            f"Requested price amount: {payload.requested_price_amount}."
        ),
    )

    db.add(audit_log)
    db.commit()
    db.refresh(price_change_request)

    return price_change_request


def get_current_applicable_standard_price(
    db: Session,
    product_id: int,
    country_id: int,
    store_id: int | None,
) -> Price | None:
    today = date.today()

    base_conditions = [
        Price.product_id == product_id,
        Price.country_id == country_id,
        Price.price_type == "STANDARD",
        Price.status == "ACTIVE",
        Price.effective_from <= today,
        (Price.effective_to.is_(None) | (Price.effective_to >= today)),
    ]

    if store_id is not None:
        query = (
            select(Price)
            .where(
                *base_conditions,
                Price.price_scope == "STORE",
                Price.store_id == store_id,
            )
            .order_by(Price.effective_from.desc())
        )
    else:
        query = (
            select(Price)
            .where(
                *base_conditions,
                Price.price_scope == "COUNTRY",
                Price.store_id.is_(None),
            )
            .order_by(Price.effective_from.desc())
        )

    return db.scalar(query)