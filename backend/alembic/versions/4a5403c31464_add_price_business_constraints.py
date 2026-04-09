"""add price business constraints

Revision ID: 4a5403c31464
Revises: a0efe46291cb
Create Date: 2026-04-08 18:51:08.028036

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4a5403c31464"
down_revision: Union[str, Sequence[str], None] = "a0efe46291cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_price_scope_values",
        "price",
        "price_scope IN ('COUNTRY', 'STORE')",
        schema="pct_core",
    )

    op.create_check_constraint(
        "ck_price_type_values",
        "price",
        "price_type IN ('STANDARD', 'PROMO')",
        schema="pct_core",
    )

    op.create_check_constraint(
        "ck_price_scope_consistency",
        "price",
        """
        (
            (price_scope = 'COUNTRY' AND country_id IS NOT NULL AND store_id IS NULL)
            OR
            (price_scope = 'STORE' AND country_id IS NOT NULL AND store_id IS NOT NULL)
        )
        """,
        schema="pct_core",
    )

    op.create_check_constraint(
        "ck_price_promotion_consistency",
        "price",
        """
        (
            (price_type = 'PROMO' AND promotion_id IS NOT NULL)
            OR
            (price_type = 'STANDARD' AND promotion_id IS NULL)
        )
        """,
        schema="pct_core",
    )

    op.create_check_constraint(
        "ck_price_effective_dates",
        "price",
        "(effective_to IS NULL OR effective_to >= effective_from)",
        schema="pct_core",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_price_effective_dates",
        "price",
        schema="pct_core",
        type_="check",
    )
    op.drop_constraint(
        "ck_price_promotion_consistency",
        "price",
        schema="pct_core",
        type_="check",
    )
    op.drop_constraint(
        "ck_price_scope_consistency",
        "price",
        schema="pct_core",
        type_="check",
    )
    op.drop_constraint(
        "ck_price_type_values",
        "price",
        schema="pct_core",
        type_="check",
    )
    op.drop_constraint(
        "ck_price_scope_values",
        "price",
        schema="pct_core",
        type_="check",
    )
