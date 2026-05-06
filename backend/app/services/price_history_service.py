from sqlalchemy import select
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
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    query = (
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
        query = query.where(
            PriceHistory.price_change_request_id == price_change_request_id
        )

    if product_id is not None:
        query = query.where(PriceChangeRequest.product_id == product_id)

    if country_id is not None:
        query = query.where(PriceChangeRequest.country_id == country_id)

    if store_id is not None:
        query = query.where(PriceChangeRequest.store_id == store_id)

    if applied_by_user_id is not None:
        query = query.where(PriceHistory.applied_by_user_id == applied_by_user_id)

    query = (
        query.order_by(PriceHistory.applied_at.desc())
        .offset(offset)
        .limit(limit)
    )

    rows = db.execute(query).mappings().all()

    return [dict(row) for row in rows]