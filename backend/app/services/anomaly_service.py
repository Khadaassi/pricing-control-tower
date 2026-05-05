from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.obt_sales import ObtSales
from app.schemas.anomaly import BusinessAnomalyRead


LOW_PROMOTION_REVENUE = "LOW_PROMOTION_REVENUE"


def _to_decimal(value: object) -> Decimal:
    if value is None:
        return Decimal("0.00")

    return Decimal(str(value))


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _get_severity(total_revenue: Decimal, threshold: Decimal) -> str:
    if threshold <= 0:
        return "LOW"

    revenue_ratio = total_revenue / threshold

    if revenue_ratio < Decimal("0.50"):
        return "HIGH"

    if revenue_ratio < Decimal("0.80"):
        return "MEDIUM"

    return "LOW"


def get_business_anomalies(
    db: Session,
    min_revenue: Decimal = Decimal("500.00"),
    promotion_id: int | None = None,
    product_id: int | None = None,
    store_id: int | None = None,
    limit: int = 50,
) -> list[BusinessAnomalyRead]:
    """
    Detect simple MVP business anomalies.

    Rule:
    A promotion is flagged as anomalous when its total revenue is below
    the configured minimum revenue threshold.

    This is a rule-based business detection, not a machine learning model.
    """

    query = (
        select(
            ObtSales.promotion_id.label("promotion_id"),
            ObtSales.product_id.label("product_id"),
            func.count(ObtSales.transaction_id).label("sales_count"),
            func.coalesce(func.sum(ObtSales.quantity), 0).label("total_quantity"),
            func.coalesce(func.sum(ObtSales.revenue), 0).label("total_revenue"),
        )
        .where(ObtSales.is_promo.is_(True))
        .where(ObtSales.promotion_id.is_not(None))
        .group_by(ObtSales.promotion_id, ObtSales.product_id)
        .having(func.coalesce(func.sum(ObtSales.revenue), 0) < min_revenue)
        .order_by(func.coalesce(func.sum(ObtSales.revenue), 0).asc())
        .limit(limit)
    )

    if promotion_id is not None:
        query = query.where(ObtSales.promotion_id == promotion_id)

    if product_id is not None:
        query = query.where(ObtSales.product_id == product_id)

    if store_id is not None:
        query = query.where(ObtSales.store_id == store_id)

    rows = db.execute(query).all()

    anomalies: list[BusinessAnomalyRead] = []

    for row in rows:
        total_revenue = _round_money(_to_decimal(row.total_revenue))
        threshold = _round_money(min_revenue)
        severity = _get_severity(total_revenue=total_revenue, threshold=threshold)

        anomalies.append(
            BusinessAnomalyRead(
                anomaly_type=LOW_PROMOTION_REVENUE,
                severity=severity,
                message=(
                    f"Promotion {row.promotion_id} generated revenue below "
                    f"the configured threshold."
                ),
                promotion_id=row.promotion_id,
                product_id=row.product_id,
                store_id=store_id,
                sales_count=int(row.sales_count or 0),
                total_quantity=int(row.total_quantity or 0),
                total_revenue=total_revenue,
                threshold=threshold,
            )
        )

    return anomalies