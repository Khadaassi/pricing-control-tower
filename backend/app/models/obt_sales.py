from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ObtSales(Base):
    __tablename__ = "obt_sales"
    __table_args__ = {"schema": "pct_analytics"}

    transaction_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    product_id: Mapped[int] = mapped_column(Integer, nullable=False)
    store_id: Mapped[int] = mapped_column(Integer, nullable=False)
    price_id: Mapped[int] = mapped_column(Integer, nullable=False)
    promotion_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    is_promo: Mapped[bool] = mapped_column(Boolean, nullable=False)
    price_scope: Mapped[str] = mapped_column(String(20), nullable=False)
    price_type: Mapped[str] = mapped_column(String(20), nullable=False)