"""create price history table

Revision ID: c37ba1f9a561
Revises: 069820c274a5
Create Date: 2026-05-05 14:05:51.942145

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c37ba1f9a561'
down_revision: Union[str, Sequence[str], None] = '069820c274a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "price_history",
        sa.Column("history_id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("price_change_request_id", sa.Integer(), nullable=False),
        sa.Column("previous_price_id", sa.Integer(), nullable=False),
        sa.Column("new_price_id", sa.Integer(), nullable=False),
        sa.Column("old_price_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("new_price_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("applied_by_user_id", sa.Integer(), nullable=False),
        sa.Column(
            "applied_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["price_change_request_id"],
            ["pct_core.price_change_request.id"],
            name="fk_price_history_price_change_request",
        ),
        sa.ForeignKeyConstraint(
            ["previous_price_id"],
            ["pct_core.price.id"],
            name="fk_price_history_previous_price",
        ),
        sa.ForeignKeyConstraint(
            ["new_price_id"],
            ["pct_core.price.id"],
            name="fk_price_history_new_price",
        ),
        sa.ForeignKeyConstraint(
            ["applied_by_user_id"],
            ["pct_core.user_account.id"],
            name="fk_price_history_applied_by_user",
        ),
        sa.CheckConstraint(
            "old_price_amount > 0",
            name="ck_price_history_old_price_positive",
        ),
        sa.CheckConstraint(
            "new_price_amount > 0",
            name="ck_price_history_new_price_positive",
        ),
        sa.CheckConstraint(
            "previous_price_id <> new_price_id",
            name="ck_price_history_previous_new_price_different",
        ),
        sa.UniqueConstraint(
            "price_change_request_id",
            name="uq_price_history_price_change_request",
        ),
        schema="pct_core",
    )

    op.create_index(
        "ix_price_history_price_change_request_id",
        "price_history",
        ["price_change_request_id"],
        schema="pct_core",
    )

    op.create_index(
        "ix_price_history_previous_price_id",
        "price_history",
        ["previous_price_id"],
        schema="pct_core",
    )

    op.create_index(
        "ix_price_history_new_price_id",
        "price_history",
        ["new_price_id"],
        schema="pct_core",
    )

    op.create_index(
        "ix_price_history_applied_by_user_id",
        "price_history",
        ["applied_by_user_id"],
        schema="pct_core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_price_history_applied_by_user_id",
        table_name="price_history",
        schema="pct_core",
    )

    op.drop_index(
        "ix_price_history_new_price_id",
        table_name="price_history",
        schema="pct_core",
    )

    op.drop_index(
        "ix_price_history_previous_price_id",
        table_name="price_history",
        schema="pct_core",
    )

    op.drop_index(
        "ix_price_history_price_change_request_id",
        table_name="price_history",
        schema="pct_core",
    )

    op.drop_table("price_history", schema="pct_core")