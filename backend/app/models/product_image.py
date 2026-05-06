from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .product import Product

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ProductImage(Base):
    __tablename__ = "product_image"
    __table_args__ = {"schema": "pct_core"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("pct_core.product.id", name="fk_product_image_product"),
        nullable=False,
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    product: Mapped["Product"] = relationship(back_populates="images")
