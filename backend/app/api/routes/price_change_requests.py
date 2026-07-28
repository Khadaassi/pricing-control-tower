from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.current_user import get_current_business_user
from app.db import get_db
from app.models.price_change_request import PriceChangeRequest
from app.models.user_account import UserAccount
from app.schemas.price_change_request import (
    PriceChangeRequestCreate,
    PriceChangeRequestRead,
    PriceChangeRequestReject,
)
from app.services.price_change_request_service import (
    approve_and_apply_price_change_request,
    create_price_change_request,
    list_price_change_requests,
    reject_price_change_request,
)
from app.services.rbac_service import ensure_user_has_permission
from app.services.scope_service import (
    ensure_country_filter_allowed,
    ensure_store_belongs_to_country_scope,
    ensure_store_filter_allowed,
)

router = APIRouter(
    prefix="/price-change-requests",
    tags=["Price Change Requests"],
)


@router.post(
    "",
    response_model=PriceChangeRequestRead,
    status_code=status.HTTP_201_CREATED,
)
def create_price_change_request_endpoint(
    payload: PriceChangeRequestCreate,
    db: Session = Depends(get_db),
    current_user: UserAccount = Depends(get_current_business_user),
) -> PriceChangeRequestRead:
    ensure_user_has_permission(
        db=db,
        user=current_user,
        permission_code="CREATE_PRICE_REQUEST",
    )

    ensure_country_filter_allowed(current_user, payload.country_id)
    ensure_store_filter_allowed(current_user, payload.store_id)
    ensure_store_belongs_to_country_scope(db, current_user, payload.store_id)

    return create_price_change_request(
        db=db,
        payload=payload,
        requested_by_user_id=current_user.id,
    )


@router.post(
    "/{price_change_request_id}/approve",
    response_model=PriceChangeRequestRead,
    status_code=status.HTTP_200_OK,
)
def approve_price_change_request_endpoint(
    price_change_request_id: int,
    db: Session = Depends(get_db),
    current_user: UserAccount = Depends(get_current_business_user),
) -> PriceChangeRequestRead:
    ensure_user_has_permission(
        db=db,
        user=current_user,
        permission_code="APPROVE_PRICE_REQUEST",
    )

    target_request = db.get(PriceChangeRequest, price_change_request_id)

    if target_request is None:
        raise HTTPException(status_code=404, detail="Price change request not found")

    ensure_country_filter_allowed(current_user, target_request.country_id)
    ensure_store_filter_allowed(current_user, target_request.store_id)
    ensure_store_belongs_to_country_scope(db, current_user, target_request.store_id)

    return approve_and_apply_price_change_request(
        db=db,
        price_change_request_id=price_change_request_id,
        performed_by_user_id=current_user.id,
    )


@router.get("")
def get_price_change_requests_endpoint(
    status: str | None = None,
    product_id: int | None = Query(default=None, gt=0),
    country_id: int | None = Query(default=None, gt=0),
    store_id: int | None = Query(default=None, gt=0),
    requested_by_user_id: int | None = Query(default=None, gt=0),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserAccount = Depends(get_current_business_user),
) -> dict:
    ensure_country_filter_allowed(current_user, country_id)
    ensure_store_filter_allowed(current_user, store_id)
    ensure_store_belongs_to_country_scope(db, current_user, store_id)

    items, total = list_price_change_requests(
        db=db,
        status=status,
        product_id=product_id,
        country_id=country_id,
        store_id=store_id,
        requested_by_user_id=requested_by_user_id,
        scope_country_id=current_user.country_id,
        scope_store_id=current_user.store_id,
        include_country_level_for_store=True,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [PriceChangeRequestRead.model_validate(item).model_dump() for item in items],
        "total": total,
    }


@router.post(
    "/{price_change_request_id}/reject",
    response_model=PriceChangeRequestRead,
    status_code=status.HTTP_200_OK,
)
def reject_price_change_request_endpoint(
    price_change_request_id: int,
    payload: PriceChangeRequestReject,
    db: Session = Depends(get_db),
    current_user: UserAccount = Depends(get_current_business_user),
) -> PriceChangeRequestRead:
    ensure_user_has_permission(
        db=db,
        user=current_user,
        permission_code="REJECT_PRICE_REQUEST",
    )

    target_request = db.get(PriceChangeRequest, price_change_request_id)

    if target_request is None:
        raise HTTPException(status_code=404, detail="Price change request not found")

    ensure_country_filter_allowed(current_user, target_request.country_id)
    ensure_store_filter_allowed(current_user, target_request.store_id)
    ensure_store_belongs_to_country_scope(db, current_user, target_request.store_id)

    return reject_price_change_request(
        db=db,
        price_change_request_id=price_change_request_id,
        rejected_by_user_id=current_user.id,
        reason=payload.reason,
    )