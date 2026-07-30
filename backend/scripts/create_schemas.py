"""Create the pct_core/pct_analytics schemas if they don't exist yet.

Not managed by Alembic itself, so this has to run before `alembic upgrade
head` on a genuinely fresh database. Mirrors the equivalent CI setup step in
.github/workflows/ci.yml. No-op on a database that already has both schemas
(e.g. the local dev volume).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.db import engine  # noqa: E402

with engine.begin() as connection:
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS pct_core"))
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS pct_analytics"))
