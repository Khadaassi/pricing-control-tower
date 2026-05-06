from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .store import Store


from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Country(Base):
    __tablename__ = "country"
    __table_args__ = {"schema": "pct_core"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    stores: Mapped[list["Store"]] = relationship(back_populates="country")
