"""update unit_price constraint to be strictly positive

Revision ID: fec186f3ed43
Revises: 1635889480e1
Create Date: 2026-04-19 11:58:55.379188

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fec186f3ed43'
down_revision: Union[str, Sequence[str], None] = '1635889480e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    # Supprimer ancienne contrainte (>= 0)
    op.drop_constraint(
        "chk_sales_transaction_unit_price_non_negative",
        "sales_transaction",
        schema="pct_core",
        type_="check",
    )

    # Ajouter nouvelle contrainte (> 0)
    op.create_check_constraint(
        "chk_sales_transaction_unit_price_positive",
        "sales_transaction",
        "unit_price > 0",
        schema="pct_core",
    )


def downgrade() -> None:
    # Supprimer nouvelle contrainte
    op.drop_constraint(
        "chk_sales_transaction_unit_price_positive",
        "sales_transaction",
        schema="pct_core",
        type_="check",
    )

    # Restaurer ancienne contrainte
    op.create_check_constraint(
        "chk_sales_transaction_unit_price_non_negative",
        "sales_transaction",
        "unit_price >= 0",
        schema="pct_core",
    )
