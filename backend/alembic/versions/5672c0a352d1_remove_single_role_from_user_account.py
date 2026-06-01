"""remove single role from user_account

Revision ID: 5672c0a352d1
Revises: 8d805af24af3
Create Date: 2026-06-01 21:24:11.833165

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5672c0a352d1'
down_revision: Union[str, Sequence[str], None] = '8d805af24af3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_user_account_role_scope",
        "user_account",
        schema="pct_core",
        type_="check",
    )

    op.drop_constraint(
        "ck_user_account_role",
        "user_account",
        schema="pct_core",
        type_="check",
    )

    op.drop_column("user_account", "role", schema="pct_core")

    op.create_check_constraint(
        "ck_user_account_scope",
        "user_account",
        "store_id IS NULL OR country_id IS NOT NULL",
        schema="pct_core",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_user_account_scope",
        "user_account",
        schema="pct_core",
        type_="check",
    )

    op.add_column(
        "user_account",
        sa.Column(
            "role",
            sa.String(length=50),
            nullable=False,
            server_default="PRICING_ANALYST",
        ),
        schema="pct_core",
    )

    op.create_check_constraint(
        "ck_user_account_role",
        "user_account",
        "role IN ('STORE_MANAGER', 'STORE_DIRECTOR', 'COUNTRY_DIRECTOR', 'PRICING_ANALYST')",
        schema="pct_core",
    )

    op.create_check_constraint(
        "ck_user_account_role_scope",
        "user_account",
        """
        (
            role IN ('STORE_MANAGER', 'STORE_DIRECTOR')
            AND country_id IS NOT NULL
            AND store_id IS NOT NULL
        )
        OR
        (
            role = 'COUNTRY_DIRECTOR'
            AND country_id IS NOT NULL
            AND store_id IS NULL
        )
        OR
        (
            role = 'PRICING_ANALYST'
            AND country_id IS NULL
            AND store_id IS NULL
        )
        """,
        schema="pct_core",
    )