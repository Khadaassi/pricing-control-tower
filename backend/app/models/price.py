from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.product import Product


class Price(Base):
    __tablename__ = "price"
    __table_args__ = {"schema": "pct_core"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Relations
    product_id: Mapped[int] = mapped_column(
        ForeignKey("pct_core.product.id"),
        nullable=False,
    )

    # Pricing fields
    price_scope: Mapped[str] = mapped_column(String(20), nullable=False)
    country_id: Mapped[int] = mapped_column(Integer, nullable=False)
    store_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    price_type: Mapped[str] = mapped_column(String(20), nullable=False)

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        server_default="EUR",
    )

    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False)

    promotion_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    # ORM relation
    product: Mapped[Product] = relationship()