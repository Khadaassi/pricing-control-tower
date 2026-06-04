from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DiscountType(str, PyEnum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_PRICE = "FIXED_PRICE"


class Promotion(Base):
    __tablename__ = "promotion"
    __table_args__ = (
        CheckConstraint(
            "discount_type IN ('PERCENTAGE', 'FIXED_PRICE')",
            name="ck_promotion_discount_type",
        ),
        {"schema": "pct_core"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Promotion business fields
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Targeted product (one promotion = one product)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("pct_core.product.id", name="fk_promotion_product"),
        nullable=False,
    )

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Geographic scope
    country_id: Mapped[int] = mapped_column(Integer, nullable=False)
    store_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Audit
    created_by: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )