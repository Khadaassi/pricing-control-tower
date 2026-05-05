"""create sales_transaction table

Revision ID: 1635889480e1
Revises: 5256d66b78d3
Create Date: 2026-04-19 11:36:18.757581

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '1635889480e1'
down_revision: Union[str, Sequence[str], None] = '5256d66b78d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sales_transaction",
        sa.Column("transaction_id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("transaction_date", sa.DateTime(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("price_id", sa.Integer(), nullable=False),
        sa.Column("promotion_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("revenue", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_promo", sa.Boolean(), nullable=False),
        sa.Column("price_scope", sa.String(length=20), nullable=False),
        sa.Column("price_type", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["pct_core.product.id"],
            name="fk_sales_transaction_product",
        ),
        sa.ForeignKeyConstraint(
            ["store_id"],
            ["pct_core.store.id"],
            name="fk_sales_transaction_store",
        ),
        sa.ForeignKeyConstraint(
            ["price_id"],
            ["pct_core.price.id"],
            name="fk_sales_transaction_price",
        ),
        sa.ForeignKeyConstraint(
            ["promotion_id"],
            ["pct_core.promotion.id"],
            name="fk_sales_transaction_promotion",
        ),
        sa.CheckConstraint("quantity > 0", name="chk_sales_transaction_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="chk_sales_transaction_unit_price_non_negative"),
        sa.CheckConstraint("revenue >= 0", name="chk_sales_transaction_revenue_non_negative"),
        sa.CheckConstraint(
            "revenue = quantity * unit_price",
            name="chk_sales_transaction_revenue_consistency",
        ),
        sa.CheckConstraint(
            "((is_promo = TRUE AND promotion_id IS NOT NULL)"
            " OR (is_promo = FALSE AND promotion_id IS NULL))",
            name="chk_sales_transaction_promo_consistency",
        ),
        sa.CheckConstraint(
            "price_scope IN ('COUNTRY', 'STORE')",
            name="chk_sales_transaction_price_scope",
        ),
        sa.CheckConstraint(
            "price_type IN ('STANDARD', 'PROMO')",
            name="chk_sales_transaction_price_type",
        ),
        schema="pct_core",
    )

    op.create_index(
        "ix_sales_transaction_transaction_date",
        "sales_transaction",
        ["transaction_date"],
        unique=False,
        schema="pct_core",
    )

    op.create_index(
        "ix_sales_transaction_product_id",
        "sales_transaction",
        ["product_id"],
        unique=False,
        schema="pct_core",
    )

    op.create_index(
        "ix_sales_transaction_store_id",
        "sales_transaction",
        ["store_id"],
        unique=False,
        schema="pct_core",
    )

    op.create_index(
        "ix_sales_transaction_promotion_id",
        "sales_transaction",
        ["promotion_id"],
        unique=False,
        schema="pct_core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_sales_transaction_promotion_id",
        table_name="sales_transaction",
        schema="pct_core",
    )
    op.drop_index(
        "ix_sales_transaction_store_id",
        table_name="sales_transaction",
        schema="pct_core",
    )
    op.drop_index(
        "ix_sales_transaction_product_id",
        table_name="sales_transaction",
        schema="pct_core",
    )
    op.drop_index(
        "ix_sales_transaction_transaction_date",
        table_name="sales_transaction",
        schema="pct_core",
    )
    op.drop_table("sales_transaction", schema="pct_core")
