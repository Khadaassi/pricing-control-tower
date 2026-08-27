from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserAccount(Base):
    __tablename__ = "user_account"
    __table_args__ = {"schema": "pct_core"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())

    # Bumped on every authenticated request (see get_current_business_user).
    # Drives the 12-month inactivity anonymization job (gdpr_retention_service).
    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    country_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("pct_core.country.id", name="fk_user_account_country"),
        nullable=True,
    )
    store_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("pct_core.store.id", name="fk_user_account_store"),
        nullable=True,
    )