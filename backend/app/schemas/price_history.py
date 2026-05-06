from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PriceHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    history_id: int
    price_change_request_id: int

    product_id: int
    country_id: int
    store_id: int | None

    previous_price_id: int
    new_price_id: int

    old_price_amount: Decimal
    new_price_amount: Decimal

    applied_by_user_id: int
    applied_at: datetime
    created_at: datetime