from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SalesTransactionRead(BaseModel):
    transaction_id: int
    transaction_date: datetime

    product_id: int
    store_id: int
    price_id: int
    promotion_id: int | None = None

    quantity: int
    unit_price: Decimal
    revenue: Decimal

    is_promo: bool

    price_scope: str
    price_type: str

    model_config = ConfigDict(from_attributes=True)