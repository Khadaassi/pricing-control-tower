"""create product_family table

Revision ID: 823e43a6d473
Revises: 5b04f599021b
Create Date: 2026-04-08 13:23:44.632277

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '823e43a6d473'
down_revision: Union[str, Sequence[str], None] = '5b04f599021b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_family",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("code", name="uq_product_family_code"),
        schema="pct_core",
    )


def downgrade() -> None:
    op.drop_table("product_family", schema="pct_core")
