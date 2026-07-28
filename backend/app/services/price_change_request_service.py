from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException
from fastapi import status as http_status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.country import Country
from app.models.price import Price
from app.models.price_change_request import PriceChangeRequest
from app.models.price_history import PriceHistory
from app.models.product import Product
from app.models.store import Store
from app.models.user_account import UserAccount
from app.schemas.price_change_request import PriceChangeRequestCreate


def create_price_change_request(
    db: Session,
    payload: PriceChangeRequestCreate,
    requested_by_user_id: int,
) -> PriceChangeRequest:
    product = db.scalar(
        select(Product).where(Product.id == payload.product_id)
    )
    if product is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    country = db.scalar(
        select(Country).where(Country.id == payload.country_id)
    )
    if country is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Country not found",
        )

    requester = db.scalar(
        select(UserAccount).where(UserAccount.id == requested_by_user_id)
    )
    if requester is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Requesting user not found",
        )

    if payload.store_id is not None:
        store = db.scalar(
            select(Store).where(Store.id == payload.store_id)
        )
        if store is None:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Store not found",
            )

        if store.country_id != payload.country_id:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Store does not belong to selected country",
            )

    current_price = get_current_applicable_standard_price(
        db=db,
        product_id=payload.product_id,
        country_id=payload.country_id,
        store_id=payload.store_id,
        as_of_date=payload.requested_effective_date,

    )

    if current_price is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
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
        requested_by_user_id=requested_by_user_id,
    )

    db.add(price_change_request)
    db.flush()

    audit_log = AuditLog(
        price_change_request_id=price_change_request.id,
        action_type="REQUEST_CREATED",
        performed_by_user_id=requested_by_user_id,
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

def list_price_change_requests(
    db: Session,
    status: str | None = None,
    product_id: int | None = None,
    country_id: int | None = None,
    store_id: int | None = None,
    requested_by_user_id: int | None = None,
    scope_country_id: int | None = None,
    scope_store_id: int | None = None,
    include_country_level_for_store: bool = False,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[PriceChangeRequest], int]:
    allowed_statuses = {
        "PENDING",
        "APPROVED",
        "REJECTED",
        "APPLIED",
        "FAILED",
    }

    if status is not None and status not in allowed_statuses:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Invalid price change request status",
        )

    query = select(PriceChangeRequest)

    if scope_country_id is not None and scope_store_id is not None:
        if include_country_level_for_store:
            query = query.where(
                PriceChangeRequest.country_id == scope_country_id,
                (
                    (PriceChangeRequest.store_id == scope_store_id)
                    | (PriceChangeRequest.store_id.is_(None))
                ),
            )
        else:
            query = query.where(PriceChangeRequest.store_id == scope_store_id)

    elif scope_country_id is not None:
        query = query.where(PriceChangeRequest.country_id == scope_country_id)

    if status is not None:
        query = query.where(PriceChangeRequest.status == status)

    if product_id is not None:
        query = query.where(PriceChangeRequest.product_id == product_id)

    if country_id is not None:
        query = query.where(PriceChangeRequest.country_id == country_id)

    if store_id is not None:
        query = query.where(PriceChangeRequest.store_id == store_id)

    if requested_by_user_id is not None:
        query = query.where(
            PriceChangeRequest.requested_by_user_id == requested_by_user_id
        )

    if date_from is not None:
        query = query.where(
            PriceChangeRequest.created_at >= datetime.combine(date_from, time.min)
        )

    if date_to is not None:
        query = query.where(
            PriceChangeRequest.created_at <= datetime.combine(date_to, time.max)
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query) or 0

    paginated_query = (
        query.order_by(PriceChangeRequest.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(paginated_query).all()), int(total)
def lock_price_change_request_for_update(
    db: Session,
    price_change_request_id: int,
) -> PriceChangeRequest | None:
    """Read a price change request row with a Postgres row lock (FOR UPDATE) held until the
    caller commits/rolls back. Shared by approve/reject so a concurrent mutation on the same
    request blocks here instead of both passing the PENDING check."""
    return db.scalar(
        select(PriceChangeRequest)
        .where(PriceChangeRequest.id == price_change_request_id)
        .with_for_update()
    )


def approve_and_apply_price_change_request(
    db: Session,
    price_change_request_id: int,
    performed_by_user_id: int,
) -> PriceChangeRequest:
    price_change_request = lock_price_change_request_for_update(db, price_change_request_id)

    if price_change_request is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Price change request not found",
        )

    if price_change_request.status != "PENDING":
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Only PENDING price change requests can be approved and applied",
        )

    performer = db.scalar(
        select(UserAccount).where(UserAccount.id == performed_by_user_id)
    )
    if performer is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Performing user not found",
        )

    current_price = db.scalar(
        select(Price).where(Price.id == price_change_request.current_price_id)
    )

    if current_price is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Current price not found",
        )

    if current_price.product_id != price_change_request.product_id:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Current price product does not match request product",
        )

    if current_price.country_id != price_change_request.country_id:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Current price country does not match request country",
        )

    if current_price.store_id != price_change_request.store_id:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Current price store does not match request store",
        )

    if current_price.price_type != "STANDARD":
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Only STANDARD prices can be changed through this workflow",
        )

    if current_price.status != "ACTIVE":
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Only ACTIVE prices can be changed through this workflow",
        )

    requested_effective_date = price_change_request.requested_effective_date

    if requested_effective_date <= current_price.effective_from:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=(
                "Requested effective date must be after the current price "
                "effective start date"
            ),
        )

    if (
        current_price.effective_to is not None
        and current_price.effective_to < requested_effective_date
    ):
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Current price is already closed before the requested effective date",
        )

    new_price_scope = (
        "STORE"
        if price_change_request.store_id is not None
        else "COUNTRY"
    )

    current_price.effective_to = requested_effective_date - timedelta(days=1)

    new_price = Price(
        product_id=price_change_request.product_id,
        country_id=price_change_request.country_id,
        store_id=price_change_request.store_id,
        price_scope=new_price_scope,
        price_type="STANDARD",
        amount=price_change_request.requested_price_amount,
        effective_from=requested_effective_date,
        effective_to=None,
        status="ACTIVE",
        promotion_id=None,
        created_by=performed_by_user_id,
    )

    db.add(new_price)
    db.flush()

    price_change_request.status = "APPLIED"

    price_history = PriceHistory(
        price_change_request_id=price_change_request.id,
        previous_price_id=current_price.id,
        new_price_id=new_price.id,
        old_price_amount=price_change_request.old_price_amount,
        new_price_amount=price_change_request.requested_price_amount,
        applied_by_user_id=performed_by_user_id,
    )

    db.add(price_history)

    audit_log = AuditLog(
        price_change_request_id=price_change_request.id,
        action_type="PRICE_APPLIED",
        performed_by_user_id=performed_by_user_id,
        description=(
            "Price change request approved and applied. "
            f"Request ID: {price_change_request.id}, "
            f"Product ID: {price_change_request.product_id}, "
            f"Country ID: {price_change_request.country_id}, "
            f"Store ID: {price_change_request.store_id}, "
            f"Previous price ID: {current_price.id}, "
            f"New price ID: {new_price.id}, "
            f"Old price amount: {price_change_request.old_price_amount}, "
            f"New price amount: {price_change_request.requested_price_amount}, "
            f"Effective date: {requested_effective_date}."
        ),
    )

    db.add(audit_log)
    db.commit()
    db.refresh(price_change_request)

    return price_change_request

def reject_price_change_request(
    db: Session,
    price_change_request_id: int,
    rejected_by_user_id: int,
    reason: str,
) -> PriceChangeRequest:
    price_change_request = lock_price_change_request_for_update(db, price_change_request_id)

    if price_change_request is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Price change request not found",
        )

    if price_change_request.status != "PENDING":
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Only PENDING price change requests can be rejected",
        )

    rejected_by_user = db.scalar(
        select(UserAccount).where(UserAccount.id == rejected_by_user_id)
    )

    if rejected_by_user is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Rejecting user not found",
        )

    cleaned_reason = reason.strip()

    if not cleaned_reason:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Rejection reason must not be empty",
        )

    try:
        price_change_request.status = "REJECTED"
        price_change_request.rejection_reason = cleaned_reason
        price_change_request.rejected_by_user_id = rejected_by_user_id
        price_change_request.rejected_at = datetime.now(timezone.utc)

        audit_log = AuditLog(
            price_change_request_id=price_change_request.id,
            action_type="REQUEST_REJECTED",
            performed_by_user_id=rejected_by_user_id,
            description=(
                "Price change request rejected. "
                f"Request ID: {price_change_request.id}, "
                f"Product ID: {price_change_request.product_id}, "
                f"Country ID: {price_change_request.country_id}, "
                f"Store ID: {price_change_request.store_id}, "
                f"Current price ID: {price_change_request.current_price_id}, "
                f"Reason: {cleaned_reason}."
            ),
        )

        db.add(audit_log)
        db.commit()
        db.refresh(price_change_request)

        return price_change_request

    except Exception:
        db.rollback()
        raise

def get_current_applicable_standard_price(
    db: Session,
    product_id: int,
    country_id: int,
    store_id: int | None,
    as_of_date: date | None = None,
) -> Price | None:
    reference_date = as_of_date or date.today()

    base_conditions = [
        Price.product_id == product_id,
        Price.country_id == country_id,
        Price.price_type == "STANDARD",
        Price.status == "ACTIVE",
        Price.effective_from <= reference_date,
        (
            Price.effective_to.is_(None)
            | (Price.effective_to >= reference_date)
        ),
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

