from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SalesTransaction(Base):
    __tablename__ = "sales_transaction"
    __table_args__ = {"schema": "pct_core"}

    transaction_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pct_core.product.id"),
        nullable=False,
    )
    store_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pct_core.store.id"),
        nullable=False,
    )
    price_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pct_core.price.id"),
        nullable=False,
    )
    promotion_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("pct_core.promotion.id"),
        nullable=True,
    )

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    is_promo: Mapped[bool] = mapped_column(Boolean, nullable=False)

    price_scope: Mapped[str] = mapped_column(String(20), nullable=False)
    price_type: Mapped[str] = mapped_column(String(20), nullable=False)