from __future__ import annotations

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RolePermission(Base):
    __tablename__ = "role_permission"
    __table_args__ = {"schema": "pct_core"}

    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pct_core.role.id", name="fk_role_permission_role", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "pct_core.permission.id",
            name="fk_role_permission_permission",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )