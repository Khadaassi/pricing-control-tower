from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.price_history import PriceHistory
from app.models.user_account import UserAccount

logger = logging.getLogger("app.gdpr_retention")

# Retention targets documented in the E1 report (C4, "RGPD et traçabilité").
INACTIVITY_RETENTION = timedelta(days=365)
HISTORY_RETENTION = timedelta(days=3 * 365)

ANONYMIZED_EMAIL_DOMAIN = "deleted.pricing-control-tower.local"
ANONYMIZED_FULL_NAME = "Utilisateur anonymisé"


@dataclass(frozen=True)
class GdprRetentionResult:
    anonymized_users: int
    purged_audit_log_rows: int
    purged_price_history_rows: int


def anonymize_inactive_users(
    db: Session,
    inactivity_retention: timedelta = INACTIVITY_RETENTION,
    now: datetime | None = None,
) -> int:
    """Anonymizes accounts inactive for more than `inactivity_retention`.

    Only accounts with a recorded `last_active_at` are eligible: an account that
    has never made an authenticated request (last_active_at is NULL) predates
    this mechanism or was never used, and is left untouched rather than guessed
    at — a deliberate, documented limit of this first automation pass.

    The row itself is never deleted (audit_log/price_history keep referencing
    the same user id); only the identifying fields are overwritten.
    """
    now = now or datetime.now(UTC)
    cutoff = now - inactivity_retention

    inactive_users = (
        db.query(UserAccount)
        .filter(
            UserAccount.active.is_(True),
            UserAccount.last_active_at.is_not(None),
            UserAccount.last_active_at < cutoff,
        )
        .all()
    )

    for user in inactive_users:
        user.email = f"anonymized-user-{user.id}@{ANONYMIZED_EMAIL_DOMAIN}"
        user.full_name = ANONYMIZED_FULL_NAME
        user.active = False

    db.commit()

    if inactive_users:
        logger.info(
            "gdpr_users_anonymized",
            extra={"count": len(inactive_users), "cutoff": cutoff.isoformat()},
        )

    return len(inactive_users)


def purge_old_history(
    db: Session,
    history_retention: timedelta = HISTORY_RETENTION,
    now: datetime | None = None,
) -> tuple[int, int]:
    """Deletes audit_log/price_history rows older than `history_retention`.

    These two tables are pure, terminal audit trails (nothing else has a
    foreign key onto their rows), so a hard delete past the retention window
    doesn't touch referential integrity elsewhere in pct_core.
    """
    now = now or datetime.now(UTC)
    cutoff = now - history_retention

    audit_log_result = db.execute(
        delete(AuditLog).where(AuditLog.created_at < cutoff)
    )
    price_history_result = db.execute(
        delete(PriceHistory).where(PriceHistory.created_at < cutoff)
    )
    db.commit()

    purged_audit_log_rows = audit_log_result.rowcount or 0
    purged_price_history_rows = price_history_result.rowcount or 0

    if purged_audit_log_rows or purged_price_history_rows:
        logger.info(
            "gdpr_history_purged",
            extra={
                "audit_log_rows": purged_audit_log_rows,
                "price_history_rows": purged_price_history_rows,
                "cutoff": cutoff.isoformat(),
            },
        )

    return purged_audit_log_rows, purged_price_history_rows


def run_gdpr_retention_cleanup(
    db: Session, now: datetime | None = None
) -> GdprRetentionResult:
    """Entry point called daily by app/core/scheduler.py."""
    anonymized_users = anonymize_inactive_users(db, now=now)
    purged_audit_log_rows, purged_price_history_rows = purge_old_history(db, now=now)

    return GdprRetentionResult(
        anonymized_users=anonymized_users,
        purged_audit_log_rows=purged_audit_log_rows,
        purged_price_history_rows=purged_price_history_rows,
    )
