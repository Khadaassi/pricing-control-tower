from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from app.db import SessionLocal

router = APIRouter(tags=["Technical"])

APP_NAME = "pricing-control-tower-api"
APP_VERSION = "0.1.0"


@router.get("/health")
def health_check() -> dict[str, Any]:
    database_check = check_database_connection()

    global_status = (
        "ok"
        if database_check["status"] == "ok"
        else "degraded"
    )

    return {
        "status": global_status,
        "service": APP_NAME,
        "version": APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "database": database_check,
        },
    }


def check_database_connection() -> dict[str, str]:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "type": "postgresql",
        }

    except Exception as exc:
        return {
            "status": "error",
            "type": "postgresql",
            "error": str(exc),
        }