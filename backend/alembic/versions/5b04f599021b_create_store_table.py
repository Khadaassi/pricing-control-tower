"""create store table

Revision ID: 5b04f599021b
Revises: 398e5ddd088e
Create Date: 2026-04-08 13:08:12.821407

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5b04f599021b"
down_revision: Union[str, Sequence[str], None] = "398e5ddd088e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "store",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("country_id", sa.Integer(), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("region", sa.String(length=255), nullable=True),
        sa.Column("opening_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(
            ["country_id"],
            ["pct_core.country.id"],
            name="fk_store_country",
        ),
        sa.UniqueConstraint("code", name="uq_store_code"),
        schema="pct_core",
    )


def downgrade() -> None:
    op.drop_table("store", schema="pct_core")
