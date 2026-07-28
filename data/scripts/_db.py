"""Shared DATABASE_URL resolution for the data/scripts/ pipeline.

Sibling module, not a package — imported as `from _db import get_database_url` by scripts
run directly (`python data/scripts/foo.py`), which puts this directory on sys.path.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")

    if not url:
        env_path = REPO_ROOT / "backend" / ".env"
        if env_path.exists():
            for raw in env_path.read_text().splitlines():
                line = raw.strip()
                if line.startswith("DATABASE_URL="):
                    url = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

    if not url:
        raise RuntimeError("DATABASE_URL is not set. Export it or add it to backend/.env.")

    return url
