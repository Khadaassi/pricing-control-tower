import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set.")

    return database_url


def get_internal_auth_secret() -> str:
    internal_auth_secret = os.getenv("INTERNAL_AUTH_SECRET")

    if not internal_auth_secret:
        raise RuntimeError("INTERNAL_AUTH_SECRET environment variable is not set.")

    return internal_auth_secret


def is_gdpr_retention_enabled() -> bool:
    """Gates the in-process APScheduler job (app/core/scheduler.py).

    Defaults to enabled everywhere (local dev, GCP) so the RGPD retention policy
    documented in the E1 report (C4) actually runs. Set to "false" in the test
    environment to keep unit tests free of a background thread touching the DB.
    """
    return os.getenv("GDPR_RETENTION_ENABLED", "true").lower() != "false"
