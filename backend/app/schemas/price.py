from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PriceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    product_id: int
    product_code: str
    product_name: str

    price_scope: str
    country_id: int
    store_id: int | None

    price_type: str

    amount: Decimal
    currency_code: str

    effective_from: date
    effective_to: date | None

    status: str

    promotion_id: int | None