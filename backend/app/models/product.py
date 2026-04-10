from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.product_family import ProductFamily


class Product(Base):
    __tablename__ = "product"
    __table_args__ = {"schema": "pct_core"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())
    product_family_id: Mapped[int] = mapped_column(
        ForeignKey("pct_core.product_family.id", name="fk_product_family"),
        nullable=False,
    )

    family: Mapped[ProductFamily] = relationship(
        back_populates="products",
    )