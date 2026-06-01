from __future__ import annotations

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserRole(Base):
    __tablename__ = "user_role"
    __table_args__ = {"schema": "pct_core"}

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pct_core.user_account.id", name="fk_user_role_user", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pct_core.role.id", name="fk_user_role_role", ondelete="CASCADE"),
        primary_key=True,
    )