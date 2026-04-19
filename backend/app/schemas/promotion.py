from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PromotionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None

    discount_type: str
    discount_value: Decimal

    start_date: date
    end_date: date

    country_id: int
    store_id: int | None

    active: bool