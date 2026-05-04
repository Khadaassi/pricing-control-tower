"""add product_id and discount_type check to promotion

Revision ID: c7a1e2f39b04
Revises: fec186f3ed43
Create Date: 2026-05-04 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7a1e2f39b04"
down_revision: Union[str, Sequence[str], None] = "fec186f3ed43"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add product_id column (NOT NULL with temporary default for existing rows)
    op.add_column(
        "promotion",
        sa.Column("product_id", sa.Integer(), nullable=False, server_default="1"),
        schema="pct_core",
    )

    # Remove the server_default after column creation
    op.alter_column(
        "promotion",
        "product_id",
        existing_type=sa.Integer(),
        server_default=None,
        schema="pct_core",
    )

    # Add foreign key to product
    op.create_foreign_key(
        "fk_promotion_product",
        "promotion",
        "product",
        ["product_id"],
        ["id"],
        source_schema="pct_core",
        referent_schema="pct_core",
    )

    # Normalize existing discount_type values before adding constraint
    op.execute(
        """
        UPDATE pct_core.promotion
        SET discount_type = 'PERCENTAGE'
        WHERE discount_type NOT IN ('PERCENTAGE', 'FIXED_PRICE')
        """
    )

    # Add CHECK constraint on discount_type
    op.create_check_constraint(
        "ck_promotion_discount_type",
        "promotion",
        "discount_type IN ('PERCENTAGE', 'FIXED_PRICE')",
        schema="pct_core",
    )

    # Update existing rows from PERCENTAGE (already valid) - no action needed
    # If there were other values, we would UPDATE them here


def downgrade() -> None:
    op.drop_constraint(
        "ck_promotion_discount_type",
        "promotion",
        schema="pct_core",
        type_="check",
    )

    op.drop_constraint(
        "fk_promotion_product",
        "promotion",
        schema="pct_core",
        type_="foreignkey",
    )

    op.drop_column("promotion", "product_id", schema="pct_core")
