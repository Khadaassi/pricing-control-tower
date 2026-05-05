from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.obt_sales import ObtSales
from app.schemas.kpi import SalesKpiRead


def _to_decimal(value: object) -> Decimal:
    if value is None:
        return Decimal("0.00")

    return Decimal(str(value))


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _round_ratio(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def get_sales_kpis(
    db: Session,
    product_id: int | None = None,
    store_id: int | None = None,
    is_promo: bool | None = None,
    price_type: str | None = None,
) -> SalesKpiRead:
    query = select(
        func.count(ObtSales.transaction_id).label("total_sales_count"),
        func.coalesce(func.sum(ObtSales.quantity), 0).label("total_quantity"),
        func.coalesce(func.sum(ObtSales.revenue), 0).label("total_revenue"),
        func.coalesce(
            func.sum(
                case(
                    (ObtSales.is_promo.is_(True), 1),
                    else_=0,
                )
            ),
            0,
        ).label("promo_sales_count"),
        func.coalesce(
            func.sum(
                case(
                    (ObtSales.is_promo.is_(True), ObtSales.revenue),
                    else_=0,
                )
            ),
            0,
        ).label("promo_revenue"),
    )

    if product_id is not None:
        query = query.where(ObtSales.product_id == product_id)

    if store_id is not None:
        query = query.where(ObtSales.store_id == store_id)

    if is_promo is not None:
        query = query.where(ObtSales.is_promo == is_promo)

    if price_type is not None:
        query = query.where(ObtSales.price_type == price_type.upper())

    result = db.execute(query).one()

    total_sales_count = int(result.total_sales_count or 0)
    total_quantity = int(result.total_quantity or 0)
    total_revenue = _to_decimal(result.total_revenue)
    promo_sales_count = int(result.promo_sales_count or 0)
    promo_revenue = _to_decimal(result.promo_revenue)

    if total_sales_count == 0:
        promo_sales_share = Decimal("0.0000")
        average_order_value = Decimal("0.00")
    else:
        promo_sales_share = _round_ratio(
            Decimal(promo_sales_count) / Decimal(total_sales_count)
        )
        average_order_value = _round_money(
            total_revenue / Decimal(total_sales_count)
        )

    return SalesKpiRead(
        total_sales_count=total_sales_count,
        total_quantity=total_quantity,
        total_revenue=_round_money(total_revenue),
        promo_sales_count=promo_sales_count,
        promo_revenue=_round_money(promo_revenue),
        promo_sales_share=promo_sales_share,
        average_order_value=average_order_value,
    )