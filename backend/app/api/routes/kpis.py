from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.kpi import SalesKpiRead
from app.services.kpi_service import get_sales_kpis

router = APIRouter(prefix="/kpis", tags=["kpis"])


@router.get(
    "",
    response_model=SalesKpiRead,
    summary="Get MVP sales KPIs",
    description="Return the main MVP sales KPIs from the analytical sales model.",
)
def read_sales_kpis(
    db: Annotated[Session, Depends(get_db)],
    product_id: int | None = Query(default=None, description="Filter by product ID"),
    store_id: int | None = Query(default=None, description="Filter by store ID"),
    is_promo: bool | None = Query(default=None, description="Filter promotional sales"),
    price_type: str | None = Query(
        default=None,
        description="Filter by price type, for example STANDARD or PROMO",
    ),
) -> SalesKpiRead:
    return get_sales_kpis(
        db=db,
        product_id=product_id,
        store_id=store_id,
        is_promo=is_promo,
        price_type=price_type,
    )