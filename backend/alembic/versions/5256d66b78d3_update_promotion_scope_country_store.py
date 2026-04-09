"""update promotion scope country/store

Revision ID: 5256d66b78d3
Revises: f5d30b494f15
Create Date: 2026-04-08 19:43:49.907618

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5256d66b78d3"
down_revision: Union[str, Sequence[str], None] = "4a5403c31464"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "promotion",
        sa.Column("country_id", sa.Integer(), nullable=False, server_default="1"),
        schema="pct_core",
    )

    op.create_foreign_key(
        "fk_promotion_country",
        "promotion",
        "country",
        ["country_id"],
        ["id"],
        source_schema="pct_core",
        referent_schema="pct_core",
    )

    op.alter_column(
        "promotion",
        "store_id",
        existing_type=sa.Integer(),
        nullable=True,
        schema="pct_core",
    )

    op.alter_column(
        "promotion",
        "country_id",
        existing_type=sa.Integer(),
        server_default=None,
        schema="pct_core",
    )


def downgrade() -> None:
    op.alter_column(
        "promotion",
        "store_id",
        existing_type=sa.Integer(),
        nullable=False,
        schema="pct_core",
    )

    op.drop_constraint(
        "fk_promotion_country",
        "promotion",
        schema="pct_core",
        type_="foreignkey",
    )

    op.drop_column("promotion", "country_id", schema="pct_core")
