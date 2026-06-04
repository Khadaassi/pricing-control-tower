from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db

router = APIRouter(prefix="/analytics/sales", tags=["analytics"])


@router.get(
    "/summary",
    summary="Analytical KPI summary by product",
    description="KPI aggregates from pct_analytics.obt_sales for a given product.",
)
def get_analytics_sales_summary(
    db: Annotated[Session, Depends(get_db)],
    product_id: int = Query(..., description="Product ID"),
) -> dict:
    sql = text("""
        SELECT
            COUNT(*)                                            AS transaction_count,
            COALESCE(SUM(quantity), 0)                         AS total_quantity,
            COALESCE(SUM(revenue), 0)                          AS total_revenue,
            COALESCE(AVG(unit_price), 0)                       AS avg_selling_price,
            COUNT(*) FILTER (WHERE is_promo = true)            AS promo_transactions,
            COALESCE(SUM(revenue) FILTER (WHERE is_promo = true), 0) AS promo_revenue,
            MIN(transaction_day)                               AS first_sale_date,
            MAX(transaction_day)                               AS last_sale_date
        FROM pct_analytics.obt_sales
        WHERE product_id = :product_id
    """)
    row = db.execute(sql, {"product_id": product_id}).mappings().one_or_none()
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
) -> dict:
    conditions = ["1=1"]
    filter_params: dict = {}

    if product_id is not None:
        conditions.append("product_id = :product_id")
        filter_params["product_id"] = product_id

    if store_id is not None:
        conditions.append("store_id = :store_id")
        filter_params["store_id"] = store_id

    if country_id is not None:
        conditions.append("country_id = :country_id")
        filter_params["country_id"] = country_id

    if is_promo is not None:
        conditions.append("is_promo = :is_promo")
        filter_params["is_promo"] = is_promo

    if date_from is not None:
        conditions.append("transaction_day >= :date_from")
        filter_params["date_from"] = date_from

    if date_to is not None:
        conditions.append("transaction_day <= :date_to")
        filter_params["date_to"] = date_to

    where = " AND ".join(conditions)

    count_sql = text(f"SELECT COUNT(*) FROM pct_analytics.obt_sales WHERE {where}")
    count_row = db.execute(count_sql, filter_params).fetchone()
    total = int(count_row[0]) if count_row else 0

    params = {**filter_params, "limit": limit, "offset": offset}
    sql = text(f"""
        SELECT
            transaction_id,
            transaction_date,
            transaction_day,
            transaction_month,
            product_id,
            product_code,
            product_name,
            brand,
            product_family_name,
            store_id,
            store_name,
            city,
            region,
            country_id,
            country_code,
            country_name,
            price_amount,
            currency_code,
            price_scope,
            price_type,
            is_store_specific_price,
            is_promotional_price,
            unit_price,
            price_difference,
            price_difference_rate,
            promotion_code,
            promotion_name,
            discount_type,
            discount_value,
            is_promo,
            has_promotion,
            quantity,
            revenue
        FROM pct_analytics.obt_sales
        WHERE {where}
        ORDER BY transaction_date DESC
        LIMIT :limit
        OFFSET :offset
    """)

    rows = db.execute(sql, params).mappings().all()
    return {"items": [dict(row) for row in rows], "total": total}
