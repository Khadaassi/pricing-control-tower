"""add price change request constraints

Revision ID: 069820c274a5
Revises: 68b888fcb0b3
Create Date: 2026-05-05 13:56:02.389643

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '069820c274a5'
down_revision: Union[str, Sequence[str], None] = '68b888fcb0b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.create_check_constraint(
        "ck_price_change_request_status",
        "price_change_request",
        "status IN ('PENDING', 'APPROVED', 'REJECTED', 'APPLIED', 'FAILED')",
        schema="pct_core",
    )

    op.create_check_constraint(
        "ck_price_change_request_old_price_positive",
        "price_change_request",
        "old_price_amount > 0",
        schema="pct_core",
    )

    op.create_check_constraint(
        "ck_price_change_request_requested_price_positive",
        "price_change_request",
        "requested_price_amount > 0",
        schema="pct_core",
    )

    op.create_check_constraint(
        "ck_price_change_request_justification_not_empty",
        "price_change_request",
        "length(trim(justification)) > 0",
        schema="pct_core",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_price_change_request_justification_not_empty",
        "price_change_request",
        schema="pct_core",
        type_="check",
    )

    op.drop_constraint(
        "ck_price_change_request_requested_price_positive",
        "price_change_request",
        schema="pct_core",
        type_="check",
    )

    op.drop_constraint(
        "ck_price_change_request_old_price_positive",
        "price_change_request",
        schema="pct_core",
        type_="check",
    )

    op.drop_constraint(
        "ck_price_change_request_status",
        "price_change_request",
        schema="pct_core",
        type_="check",
    )