from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Identity, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PriceChangeRequest(Base):
    __tablename__ = "price_change_request"
    __table_args__ = {"schema": "pct_core"}

    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)

    product_id: Mapped[int] = mapped_column(
        ForeignKey("pct_core.product.id", name="fk_price_change_request_product"),
        nullable=False,
        index=True,
    )

    country_id: Mapped[int] = mapped_column(
        ForeignKey("pct_core.country.id", name="fk_price_change_request_country"),
        nullable=False,
        index=True,
    )

    store_id: Mapped[int | None] = mapped_column(
        ForeignKey("pct_core.store.id", name="fk_price_change_request_store"),
        nullable=True,
        index=True,
    )

    current_price_id: Mapped[int] = mapped_column(
        ForeignKey("pct_core.price.id", name="fk_price_change_request_current_price"),
        nullable=False,
    )

    old_price_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    requested_price_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="PENDING",
        index=True,
    )

    justification: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    requested_effective_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    requested_by_user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "pct_core.user_account.id",
            name="fk_price_change_request_requested_by_user",
        ),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    product = relationship("Product")
    current_price = relationship("Price")