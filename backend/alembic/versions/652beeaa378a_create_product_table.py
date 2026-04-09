"""create product table

Revision ID: 652beeaa378a
Revises: 823e43a6d473
Create Date: 2026-04-08 13:30:57.448719

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "652beeaa378a"
down_revision: Union[str, Sequence[str], None] = "823e43a6d473"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("brand", sa.String(length=100), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("product_family_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_family_id"],
            ["pct_core.product_family.id"],
            name="fk_product_family",
        ),
        sa.UniqueConstraint("code", name="uq_product_code"),
        schema="pct_core",
    )


def downgrade() -> None:
    op.drop_table("product", schema="pct_core")
