from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = {"schema": "pct_core"}

    history_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    price_change_request_id: Mapped[int] = mapped_column(
        ForeignKey(
            "pct_core.price_change_request.id",
            name="fk_price_history_price_change_request",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    previous_price_id: Mapped[int] = mapped_column(
        ForeignKey("pct_core.price.id", name="fk_price_history_previous_price"),
        nullable=False,
        index=True,
    )

    new_price_id: Mapped[int] = mapped_column(
        ForeignKey("pct_core.price.id", name="fk_price_history_new_price"),
        nullable=False,
        index=True,
    )

    old_price_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    new_price_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    applied_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("pct_core.user_account.id", name="fk_price_history_applied_by_user"),
        nullable=False,
        index=True,
    )

    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    price_change_request = relationship("PriceChangeRequest")
    previous_price = relationship("Price", foreign_keys=[previous_price_id])
    new_price = relationship("Price", foreign_keys=[new_price_id])