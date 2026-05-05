"""create audit log table

Revision ID: 63cb3004e2e5
Revises: c37ba1f9a561
Create Date: 2026-05-05 14:20:30.545725

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '63cb3004e2e5'
down_revision: Union[str, Sequence[str], None] = 'c37ba1f9a561'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("audit_id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("price_change_request_id", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("performed_by_user_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["price_change_request_id"],
            ["pct_core.price_change_request.id"],
            name="fk_audit_log_price_change_request",
        ),
        sa.ForeignKeyConstraint(
            ["performed_by_user_id"],
            ["pct_core.user_account.id"],
            name="fk_audit_log_performed_by_user",
        ),
        sa.CheckConstraint(
            "action_type IN ("
            "'REQUEST_CREATED', "
            "'REQUEST_APPROVED', "
            "'REQUEST_REJECTED', "
            "'PRICE_APPLIED', "
            "'PRICE_APPLICATION_FAILED'"
            ")",
            name="ck_audit_log_action_type",
        ),
        sa.CheckConstraint(
            "length(trim(description)) > 0",
            name="ck_audit_log_description_not_empty",
        ),
        schema="pct_core",
    )

    op.create_index(
        "ix_audit_log_price_change_request_id",
        "audit_log",
        ["price_change_request_id"],
        schema="pct_core",
    )

    op.create_index(
        "ix_audit_log_performed_by_user_id",
        "audit_log",
        ["performed_by_user_id"],
        schema="pct_core",
    )

    op.create_index(
        "ix_audit_log_action_type",
        "audit_log",
        ["action_type"],
        schema="pct_core",
    )

    op.create_index(
        "ix_audit_log_created_at",
        "audit_log",
        ["created_at"],
        schema="pct_core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_audit_log_created_at",
        table_name="audit_log",
        schema="pct_core",
    )

    op.drop_index(
        "ix_audit_log_action_type",
        table_name="audit_log",
        schema="pct_core",
    )

    op.drop_index(
        "ix_audit_log_performed_by_user_id",
        table_name="audit_log",
        schema="pct_core",
    )

    op.drop_index(
        "ix_audit_log_price_change_request_id",
        table_name="audit_log",
        schema="pct_core",
    )

    op.drop_table("audit_log", schema="pct_core")