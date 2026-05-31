"""add rbac fields to user_account

Revision ID: f984259217d9
Revises: ce9a2d7a81b5
Create Date: 2026-05-31 12:52:18.760982

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f984259217d9'
down_revision: Union[str, Sequence[str], None] = 'ce9a2d7a81b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ROLE_VALUES = (
    "STORE_MANAGER",
    "STORE_DIRECTOR",
    "COUNTRY_DIRECTOR",
    "PRICING_ANALYST",
)


def upgrade() -> None:
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

    op.add_column(
        "user_account",
        sa.Column("country_id", sa.Integer(), nullable=True),
        schema="pct_core",
    )

    op.add_column(
        "user_account",
        sa.Column("store_id", sa.Integer(), nullable=True),
        schema="pct_core",
    )

    op.create_foreign_key(
        "fk_user_account_country",
        source_table="user_account",
        referent_table="country",
        local_cols=["country_id"],
        remote_cols=["id"],
        source_schema="pct_core",
        referent_schema="pct_core",
    )

    op.create_foreign_key(
        "fk_user_account_store",
        source_table="user_account",
        referent_table="store",
        local_cols=["store_id"],
        remote_cols=["id"],
        source_schema="pct_core",
        referent_schema="pct_core",
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


def downgrade() -> None:
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

    op.drop_constraint(
        "fk_user_account_store",
        "user_account",
        schema="pct_core",
        type_="foreignkey",
    )

    op.drop_constraint(
        "fk_user_account_country",
        "user_account",
        schema="pct_core",
        type_="foreignkey",
    )

    op.drop_column("user_account", "store_id", schema="pct_core")
    op.drop_column("user_account", "country_id", schema="pct_core")
    op.drop_column("user_account", "role", schema="pct_core")