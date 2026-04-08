"""create price table

Revision ID: a0efe46291cb
Revises: dfc3ab5f2ed3
Create Date: 2026-04-08 14:20:37.785790

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0efe46291cb'
down_revision: Union[str, Sequence[str], None] = 'dfc3ab5f2ed3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "price",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("price_scope", sa.String(length=20), nullable=False),
        sa.Column("country_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=True),
        sa.Column("price_type", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("promotion_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["pct_core.product.id"],
            name="fk_price_product",
        ),
        sa.ForeignKeyConstraint(
            ["country_id"],
            ["pct_core.country.id"],
            name="fk_price_country",
        ),
        sa.ForeignKeyConstraint(
            ["store_id"],
            ["pct_core.store.id"],
            name="fk_price_store",
        ),
        sa.ForeignKeyConstraint(
            ["promotion_id"],
            ["pct_core.promotion.id"],
            name="fk_price_promotion",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["pct_core.user_account.id"],
            name="fk_price_created_by",
        ),
        schema="pct_core",
    )


def downgrade() -> None:
    op.drop_table("price", schema="pct_core")
