from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = {"schema": "pct_core"}

    audit_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    price_change_request_id: Mapped[int] = mapped_column(
        ForeignKey(
            "pct_core.price_change_request.id",
            name="fk_audit_log_price_change_request",
        ),
        nullable=False,
        index=True,
    )

    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    performed_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("pct_core.user_account.id", name="fk_audit_log_performed_by_user"),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    price_change_request = relationship("PriceChangeRequest")