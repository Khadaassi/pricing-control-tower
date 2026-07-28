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
