"""Create the pct_core/pct_analytics schemas if they don't exist yet.

Not managed by Alembic itself, so this has to run before `alembic upgrade
head` on a genuinely fresh database. Mirrors the equivalent CI setup step in
.github/workflows/ci.yml. No-op on a database that already has both schemas
(e.g. the local dev volume).
"""

from sqlalchemy import text

from app.db import engine

with engine.begin() as connection:
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS pct_core"))
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS pct_analytics"))
