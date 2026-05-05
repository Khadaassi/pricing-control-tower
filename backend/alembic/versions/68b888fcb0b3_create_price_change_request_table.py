"""create price change request table

Revision ID: 68b888fcb0b3
Revises: c7a1e2f39b04
Create Date: 2026-05-05 13:26:16.450336

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68b888fcb0b3'
down_revision: Union[str, Sequence[str], None] = 'c7a1e2f39b04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.create_table(
        "price_change_request",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), primary_key=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("country_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=True),
        sa.Column("current_price_id", sa.Integer(), nullable=False),
        sa.Column("old_price_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("requested_price_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("requested_effective_date", sa.Date(), nullable=False),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["pct_core.product.id"],
            name="fk_price_change_request_product",
        ),
        sa.ForeignKeyConstraint(
            ["country_id"],
            ["pct_core.country.id"],
            name="fk_price_change_request_country",
        ),
        sa.ForeignKeyConstraint(
            ["store_id"],
            ["pct_core.store.id"],
            name="fk_price_change_request_store",
        ),
        sa.ForeignKeyConstraint(
            ["current_price_id"],
            ["pct_core.price.id"],
            name="fk_price_change_request_current_price",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_user_id"],
            ["pct_core.user_account.id"],
            name="fk_price_change_request_requested_by_user",
        ),
        schema="pct_core",
    )

    op.create_index(
        "ix_price_change_request_product_id",
        "price_change_request",
        ["product_id"],
        schema="pct_core",
    )

    op.create_index(
        "ix_price_change_request_country_id",
        "price_change_request",
        ["country_id"],
        schema="pct_core",
    )

    op.create_index(
        "ix_price_change_request_store_id",
        "price_change_request",
        ["store_id"],
        schema="pct_core",
    )

    op.create_index(
        "ix_price_change_request_status",
        "price_change_request",
        ["status"],
        schema="pct_core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_price_change_request_status",
        table_name="price_change_request",
        schema="pct_core",
    )

    op.drop_index(
        "ix_price_change_request_store_id",
        table_name="price_change_request",
        schema="pct_core",
    )

    op.drop_index(
        "ix_price_change_request_country_id",
        table_name="price_change_request",
        schema="pct_core",
    )

    op.drop_index(
        "ix_price_change_request_product_id",
        table_name="price_change_request",
        schema="pct_core",
    )

    op.drop_table("price_change_request", schema="pct_core")