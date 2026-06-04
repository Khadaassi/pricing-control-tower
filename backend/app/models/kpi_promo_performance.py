from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class KpiPromoPerformance(Base):
    """
    Read-only dbt analytical view (pct_analytics.kpi_promo_performance).

    Grain: (country_id, store_id, product_id, promotion_id)

    Compares each promotion against the same product's behaviour
    in the 14 days before the promotion start (baseline).
    All volume/revenue metrics are normalised to daily averages
    to neutralise duration differences between the promo and baseline windows.
    """

    __tablename__ = "kpi_promo_performance"
    __table_args__ = {"schema": "pct_analytics"}

    # Composite PK — table grain
    country_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    promotion_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    product_family_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Applied discount
    discount_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    discount_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Time windows
    promotion_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    promotion_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    baseline_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    baseline_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    promo_period_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Product metrics during the promotion
    promo_quantity: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    promo_revenue: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    promo_daily_revenue: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    promo_daily_quantity: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    promo_avg_selling_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    # Product metrics over the baseline (14 days before)
    baseline_quantity: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    baseline_revenue: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    baseline_daily_revenue: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    baseline_daily_quantity: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    baseline_avg_selling_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # Uplift (signal principal d'anomalie)
    revenue_uplift_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    revenue_uplift_pct: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    quantity_uplift_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    additional_revenue: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)

    # Price effect (secondary signal)
    avg_price_discount_effect_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    # Family effect (cannibalization / halo)
    family_revenue_variation_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    family_effect_flag: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Performance flag computed by dbt
    promo_performance_flag: Mapped[str | None] = mapped_column(String(30), nullable=True)
