from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.price_change_request import PriceChangeRequest
from app.models.price_history import PriceHistory


def list_price_history(
    db: Session,
    price_change_request_id: int | None = None,
    product_id: int | None = None,
    country_id: int | None = None,
    store_id: int | None = None,
    applied_by_user_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[dict], int]:
    base_query = (
        select(
            PriceHistory.history_id,
            PriceHistory.price_change_request_id,
            PriceChangeRequest.product_id,
            PriceChangeRequest.country_id,
            PriceChangeRequest.store_id,
            PriceHistory.previous_price_id,
            PriceHistory.new_price_id,
            PriceHistory.old_price_amount,
            PriceHistory.new_price_amount,
            PriceHistory.applied_by_user_id,
            PriceHistory.applied_at,
            PriceHistory.created_at,
        )
        .join(
            PriceChangeRequest,
            PriceChangeRequest.id == PriceHistory.price_change_request_id,
        )
    )

    if price_change_request_id is not None:
        base_query = base_query.where(
            PriceHistory.price_change_request_id == price_change_request_id
        )

    if product_id is not None:
        base_query = base_query.where(PriceChangeRequest.product_id == product_id)

    if country_id is not None:
        base_query = base_query.where(PriceChangeRequest.country_id == country_id)

    if store_id is not None:
        base_query = base_query.where(PriceChangeRequest.store_id == store_id)

    if applied_by_user_id is not None:
        base_query = base_query.where(PriceHistory.applied_by_user_id == applied_by_user_id)

    if date_from is not None:
        base_query = base_query.where(PriceHistory.applied_at >= date_from)

    if date_to is not None:
        base_query = base_query.where(PriceHistory.applied_at <= date_to)

    count_query = select(func.count()).select_from(base_query.subquery())
    total = db.scalar(count_query) or 0

    rows = db.execute(
        base_query.order_by(PriceHistory.applied_at.desc())
        .offset(offset)
        .limit(limit)
    ).mappings().all()

    return [dict(row) for row in rows], int(total)