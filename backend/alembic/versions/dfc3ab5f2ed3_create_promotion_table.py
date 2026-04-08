"""create promotion table

Revision ID: dfc3ab5f2ed3
Revises: b6e75178c6ca
Create Date: 2026-04-08 13:55:12.379924

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dfc3ab5f2ed3'
down_revision: Union[str, Sequence[str], None] = 'b6e75178c6ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "promotion",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("discount_type", sa.String(length=20), nullable=False),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),

        sa.ForeignKeyConstraint(
            ["store_id"],
            ["pct_core.store.id"],
            name="fk_promotion_store",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["pct_core.user_account.id"],
            name="fk_promotion_user",
        ),

        sa.UniqueConstraint("code", name="uq_promotion_code"),

        schema="pct_core",
    )


def downgrade() -> None:
    op.drop_table("promotion", schema="pct_core")

