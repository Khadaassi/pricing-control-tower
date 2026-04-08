"""create product_image table

Revision ID: 48fe791cf98b
Revises: 652beeaa378a
Create Date: 2026-04-08 13:39:37.360306

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48fe791cf98b'
down_revision: Union[str, Sequence[str], None] = '652beeaa378a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_image",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=False),
        sa.Column("alt_text", sa.String(length=255), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["pct_core.product.id"],
            name="fk_product_image_product",
        ),
        schema="pct_core",
    )


def downgrade() -> None:
    op.drop_table("product_image", schema="pct_core")
