from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.current_user import get_current_business_user
from app.db import get_db
from app.models.user_account import UserAccount
from app.schemas.kpi import SalesKpiRead
from app.services.kpi_service import get_sales_kpis
from app.services.scope_service import (
    ensure_store_belongs_to_country_scope,
    ensure_store_filter_allowed,
    resolve_allowed_store_ids_for_analytics,
)

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
    current_user: UserAccount = Depends(get_current_business_user),
) -> SalesKpiRead:
    ensure_store_filter_allowed(current_user, store_id)
    ensure_store_belongs_to_country_scope(db, current_user, store_id)

    allowed_store_ids = resolve_allowed_store_ids_for_analytics(
        db=db,
        user=current_user,
    )

    return get_sales_kpis(
        db=db,
        product_id=product_id,
        store_id=store_id,
        allowed_store_ids=allowed_store_ids,
        is_promo=is_promo,
        price_type=price_type,
    )