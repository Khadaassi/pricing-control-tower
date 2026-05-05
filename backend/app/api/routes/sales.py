from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.sales_transaction import SalesTransaction
from app.schemas.sales_transaction import SalesTransactionRead

router = APIRouter(prefix="/sales", tags=["sales"])


@router.get(
    "",
    response_model=list[SalesTransactionRead],
    summary="List sales transactions",
    description="Return sales transaction records with simple MVP filters.",
)
def list_sales_transactions(
    db: Annotated[Session, Depends(get_db)],
    product_id: int | None = Query(default=None, description="Filter by product ID"),
    store_id: int | None = Query(default=None, description="Filter by store ID"),
    promotion_id: int | None = Query(default=None, description="Filter by promotion ID"),
    is_promo: bool | None = Query(default=None, description="Filter promotional sales"),
    price_type: str | None = Query(
        default=None,
        description="Filter by price type, for example STANDARD or PROMO",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of records to return",
    ),
) -> list[SalesTransactionRead]:
    query = select(SalesTransaction).order_by(SalesTransaction.transaction_id)

    if product_id is not None:
        query = query.where(SalesTransaction.product_id == product_id)

    if store_id is not None:
        query = query.where(SalesTransaction.store_id == store_id)

    if promotion_id is not None:
        query = query.where(SalesTransaction.promotion_id == promotion_id)

    if is_promo is not None:
        query = query.where(SalesTransaction.is_promo == is_promo)

    if price_type is not None:
        query = query.where(SalesTransaction.price_type == price_type.upper())

    query = query.limit(limit)

    sales_transactions = db.scalars(query).all()

    return list(sales_transactions)