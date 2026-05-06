"""add rejection fields to price_change_request

Revision ID: ce9a2d7a81b5
Revises: 63cb3004e2e5
Create Date: 2026-05-06 10:11:45.416715

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ce9a2d7a81b5'
down_revision: Union[str, Sequence[str], None] = '63cb3004e2e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.add_column(
        "price_change_request",
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        schema="pct_core",
    )

    op.add_column(
        "price_change_request",
        sa.Column("rejected_by_user_id", sa.Integer(), nullable=True),
        schema="pct_core",
    )

    op.add_column(
        "price_change_request",
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        schema="pct_core",
    )

    op.create_foreign_key(
        "fk_price_change_request_rejected_by_user",
        "price_change_request",
        "user_account",
        ["rejected_by_user_id"],
        ["id"],
        source_schema="pct_core",
        referent_schema="pct_core",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_price_change_request_rejected_by_user",
        "price_change_request",
        schema="pct_core",
        type_="foreignkey",
    )

    op.drop_column(
        "price_change_request",
        "rejected_at",
        schema="pct_core",
    )

    op.drop_column(
        "price_change_request",
        "rejected_by_user_id",
        schema="pct_core",
    )

    op.drop_column(
        "price_change_request",
        "rejection_reason",
        schema="pct_core",
    )
