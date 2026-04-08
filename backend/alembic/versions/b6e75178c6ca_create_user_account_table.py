"""create user_account table

Revision ID: b6e75178c6ca
Revises: 48fe791cf98b
Create Date: 2026-04-08 13:46:36.141658

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6e75178c6ca'
down_revision: Union[str, Sequence[str], None] = '48fe791cf98b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_account",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("email", name="uq_user_account_email"),
        schema="pct_core",
    )


def downgrade() -> None:
    op.drop_table("user_account", schema="pct_core")
