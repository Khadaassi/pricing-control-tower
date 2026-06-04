"""create rbac role permission tables

Revision ID: 8d805af24af3
Revises: f984259217d9
Create Date: 2026-06-01 20:44:50.046962

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d805af24af3'
down_revision: Union[str, Sequence[str], None] = 'f984259217d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "role",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("code", name="uq_role_code"),
        schema="pct_core",
    )

    op.create_table(
        "permission",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), primary_key=True),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("code", name="uq_permission_code"),
        schema="pct_core",
    )

    op.create_table(
        "user_role",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "role_id", name="pk_user_role"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["pct_core.user_account.id"],
            name="fk_user_role_user",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["pct_core.role.id"],
            name="fk_user_role_role",
            ondelete="CASCADE",
        ),
        schema="pct_core",
    )

    op.create_table(
        "role_permission",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("role_id", "permission_id", name="pk_role_permission"),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["pct_core.role.id"],
            name="fk_role_permission_role",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["pct_core.permission.id"],
            name="fk_role_permission_permission",
            ondelete="CASCADE",
        ),
        schema="pct_core",
    )


def downgrade() -> None:
    op.drop_table("role_permission", schema="pct_core")
    op.drop_table("user_role", schema="pct_core")
    op.drop_table("permission", schema="pct_core")
    op.drop_table("role", schema="pct_core")