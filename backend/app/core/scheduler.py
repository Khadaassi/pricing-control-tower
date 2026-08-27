from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.db import SessionLocal
from app.services.gdpr_retention_service import run_gdpr_retention_cleanup

logger = logging.getLogger("app.scheduler")

_scheduler: BackgroundScheduler | None = None


def _run_gdpr_retention_job() -> None:
    db = SessionLocal()
    try:
        result = run_gdpr_retention_cleanup(db)
        logger.info(
            "gdpr_retention_job_completed",
            extra={
                "anonymized_users": result.anonymized_users,
                "purged_audit_log_rows": result.purged_audit_log_rows,
                "purged_price_history_rows": result.purged_price_history_rows,
            },
        )
    except Exception:
        logger.exception("gdpr_retention_job_failed")
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    """Starts the in-process job scheduler (called once, on FastAPI startup).

    A single daily job today (GDPR retention, C4) — deliberately generic enough
    to host future recurring jobs without introducing a new component.
    """
    global _scheduler

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _run_gdpr_retention_job,
        trigger="cron",
        hour=3,
        minute=0,
        id="gdpr_retention_cleanup",
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler

    logger.info("scheduler_started", extra={"jobs": ["gdpr_retention_cleanup"]})
    return scheduler


def shutdown_scheduler() -> None:
    global _scheduler

    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
