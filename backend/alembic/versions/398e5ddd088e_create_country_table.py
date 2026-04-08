"""create country table

Revision ID: 398e5ddd088e
Revises: 1ee6860b7287
Create Date: 2026-04-08 12:55:23.637056

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '398e5ddd088e'
down_revision: Union[str, Sequence[str], None] = '1ee6860b7287'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.create_table(
        "country",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.UniqueConstraint("code", name="uq_country_code"),
        schema="pct_core",
    )


def downgrade() -> None:
    op.drop_table("country", schema="pct_core")
