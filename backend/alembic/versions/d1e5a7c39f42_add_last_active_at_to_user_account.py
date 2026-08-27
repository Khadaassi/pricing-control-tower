"""add last_active_at to user_account

Revision ID: d1e5a7c39f42
Revises: 5672c0a352d1
Create Date: 2026-08-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e5a7c39f42'
down_revision: Union[str, Sequence[str], None] = '5672c0a352d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_account",
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        schema="pct_core",
    )


def downgrade() -> None:
    op.drop_column("user_account", "last_active_at", schema="pct_core")
