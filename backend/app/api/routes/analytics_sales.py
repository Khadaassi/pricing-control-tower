from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, column, func, select, table
from sqlalchemy.orm import Session

from app.api.dependencies.current_user import get_current_business_user
from app.db import get_db
from app.models.user_account import UserAccount
from app.services.scope_service import (
    ensure_country_filter_allowed,
    ensure_store_belongs_to_country_scope,
    ensure_store_filter_allowed,
    resolve_allowed_store_ids_for_analytics,
)

router = APIRouter(prefix="/analytics/sales", tags=["analytics"])

# pct_analytics.obt_sales is a dbt-built analytical view, not an ORM-mapped model. table()/
# column() give a typed, injection-safe query surface (and_()/.where()) without needing a full
# mapped class for a view this wide.
obt_sales = table(
    "obt_sales",
    column("transaction_id"),
    column("transaction_date"),
    column("transaction_day"),
    column("transaction_month"),
    column("product_id"),
    column("product_code"),
    column("product_name"),
    column("brand"),
    column("product_family_name"),
    column("store_id"),
    column("store_name"),
    column("city"),
    column("region"),
    column("country_id"),
    column("country_code"),
    column("country_name"),
    column("price_amount"),
    column("currency_code"),
    column("price_scope"),
    column("price_type"),
    column("is_store_specific_price"),
    column("is_promotional_price"),
    column("unit_price"),
    column("price_difference"),
    column("price_difference_rate"),
    column("promotion_code"),
    column("promotion_name"),
    column("discount_type"),
    column("discount_value"),
    column("is_promo"),
    column("has_promotion"),
    column("quantity"),
    column("revenue"),
    schema="pct_analytics",
)

LIST_COLUMNS = [
    obt_sales.c.transaction_id,
    obt_sales.c.transaction_date,
    obt_sales.c.transaction_day,
    obt_sales.c.transaction_month,
    obt_sales.c.product_id,
    obt_sales.c.product_code,
    obt_sales.c.product_name,
    obt_sales.c.brand,
    obt_sales.c.product_family_name,
    obt_sales.c.store_id,
    obt_sales.c.store_name,
    obt_sales.c.city,
    obt_sales.c.region,
    obt_sales.c.country_id,
    obt_sales.c.country_code,
    obt_sales.c.country_name,
    obt_sales.c.price_amount,
    obt_sales.c.currency_code,
    obt_sales.c.price_scope,
    obt_sales.c.price_type,
    obt_sales.c.is_store_specific_price,
    obt_sales.c.is_promotional_price,
    obt_sales.c.unit_price,
    obt_sales.c.price_difference,
    obt_sales.c.price_difference_rate,
    obt_sales.c.promotion_code,
    obt_sales.c.promotion_name,
    obt_sales.c.discount_type,
    obt_sales.c.discount_value,
    obt_sales.c.is_promo,
    obt_sales.c.has_promotion,
    obt_sales.c.quantity,
    obt_sales.c.revenue,
]


@router.get(
    "/summary",
    summary="Analytical KPI summary by product",
    description="KPI aggregates from pct_analytics.obt_sales for a given product.",
)
def get_analytics_sales_summary(
    db: Annotated[Session, Depends(get_db)],
    product_id: int = Query(..., description="Product ID"),
    current_user: UserAccount = Depends(get_current_business_user),
) -> dict:
    allowed_store_ids = resolve_allowed_store_ids_for_analytics(db=db, user=current_user)

    conditions = [obt_sales.c.product_id == product_id]

    if allowed_store_ids is not None:
        conditions.append(obt_sales.c.store_id.in_(allowed_store_ids))

    is_promo = obt_sales.c.is_promo.is_(True)

    stmt = select(
        func.count().label("transaction_count"),
        func.coalesce(func.sum(obt_sales.c.quantity), 0).label("total_quantity"),
        func.coalesce(func.sum(obt_sales.c.revenue), 0).label("total_revenue"),
        func.coalesce(func.avg(obt_sales.c.unit_price), 0).label("avg_selling_price"),
        func.count().filter(is_promo).label("promo_transactions"),
        func.coalesce(func.sum(obt_sales.c.revenue).filter(is_promo), 0).label("promo_revenue"),
        func.min(obt_sales.c.transaction_day).label("first_sale_date"),
        func.max(obt_sales.c.transaction_day).label("last_sale_date"),
    ).where(and_(*conditions))

    row = db.execute(stmt).mappings().one_or_none()
    if row is None or row["transaction_count"] == 0:
        return {"product_id": product_id, "transaction_count": 0}

    total = float(row["total_revenue"])
    promo = float(row["promo_revenue"])
    count = int(row["transaction_count"])
    promo_count = int(row["promo_transactions"])

    return {
        "product_id": product_id,
        "transaction_count": count,
        "total_quantity": int(row["total_quantity"]),
        "total_revenue": round(total, 2),
        "avg_selling_price": round(float(row["avg_selling_price"]), 2),
        "promo_transactions": promo_count,
        "promo_revenue": round(promo, 2),
        "promo_share_pct": round(promo_count / count * 100, 1) if count else 0,
        "first_sale_date": str(row["first_sale_date"]) if row["first_sale_date"] else None,
        "last_sale_date": str(row["last_sale_date"]) if row["last_sale_date"] else None,
    }


@router.get(
    "",
    summary="Analytical OBT sales",
    description="Enriched sales records from pct_analytics.obt_sales.",
)
def list_analytics_sales(
    db: Annotated[Session, Depends(get_db)],
    product_id: int | None = Query(default=None),
    store_id: int | None = Query(default=None),
    country_id: int | None = Query(default=None),
    is_promo: bool | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    current_user: UserAccount = Depends(get_current_business_user),
) -> dict:
    ensure_country_filter_allowed(current_user, country_id)
    ensure_store_filter_allowed(current_user, store_id)
    ensure_store_belongs_to_country_scope(db, current_user, store_id)

    allowed_store_ids = resolve_allowed_store_ids_for_analytics(db=db, user=current_user)

    conditions = []

    if product_id is not None:
        conditions.append(obt_sales.c.product_id == product_id)

    if store_id is not None:
        conditions.append(obt_sales.c.store_id == store_id)
    elif allowed_store_ids is not None:
        conditions.append(obt_sales.c.store_id.in_(allowed_store_ids))

    if country_id is not None:
        conditions.append(obt_sales.c.country_id == country_id)

    if is_promo is not None:
        conditions.append(obt_sales.c.is_promo == is_promo)

    if date_from is not None:
        conditions.append(obt_sales.c.transaction_day >= date_from)

    if date_to is not None:
        conditions.append(obt_sales.c.transaction_day <= date_to)

    count_stmt = select(func.count()).select_from(obt_sales)
    list_stmt = select(*LIST_COLUMNS).select_from(obt_sales)

    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
        list_stmt = list_stmt.where(and_(*conditions))

    total = db.scalar(count_stmt) or 0

    list_stmt = (
        list_stmt.order_by(obt_sales.c.transaction_date.desc()).limit(limit).offset(offset)
    )

    rows = db.execute(list_stmt).mappings().all()
    return {"items": [dict(row) for row in rows], "total": total}
