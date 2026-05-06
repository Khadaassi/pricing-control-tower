from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Store(Base):
    __tablename__ = "store"
    __table_args__ = {"schema": "pct_core"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    country_id: Mapped[int] = mapped_column(
        ForeignKey("pct_core.country.id", name="fk_store_country"),
        nullable=False,
    )
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    opening_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    country: Mapped["Country"] = relationship(back_populates="stores")
