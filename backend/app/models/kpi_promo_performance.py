from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class KpiPromoPerformance(Base):
    """
    Vue analytique dbt (pct_analytics.kpi_promo_performance) — lecture seule.

    Grain : (country_id, store_id, product_id, promotion_id)

    Compare chaque promotion au comportement du même produit
    sur les 14 jours précédant le début de la promotion (baseline).
    Toutes les métriques de volume/CA sont normalisées en moyennes journalières
    pour neutraliser les différences de durée entre la promo et le baseline.
    """

    __tablename__ = "kpi_promo_performance"
    __table_args__ = {"schema": "pct_analytics"}

    # Composite PK — grain de la table
    country_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    promotion_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    product_family_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Remise appliquée
    discount_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    discount_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Fenêtres temporelles
    promotion_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    promotion_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    baseline_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    baseline_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    promo_period_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Métriques produit pendant la promo
    promo_quantity: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    promo_revenue: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    promo_daily_revenue: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    promo_daily_quantity: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    promo_avg_selling_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    # Métriques produit sur le baseline (14j avant)
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

    # Effet prix (signal secondaire)
    avg_price_discount_effect_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    # Effet famille (cannibalization / halo)
    family_revenue_variation_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    family_effect_flag: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Flag de performance calculé par dbt
    promo_performance_flag: Mapped[str | None] = mapped_column(String(30), nullable=True)
