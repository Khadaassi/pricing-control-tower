from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict


class DiscountTypeEnum(str, Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_PRICE = "FIXED_PRICE"


class PromotionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None

    discount_type: DiscountTypeEnum
    discount_value: Decimal

    product_id: int

    start_date: date
    end_date: date

    country_id: int
    store_id: int | None

    active: bool


class PromotionCreate(BaseModel):
    code: str
    name: str
    description: str | None = None
    discount_type: DiscountTypeEnum
    discount_value: Decimal
    product_id: int
    start_date: date
    end_date: date
    country_id: int
    store_id: int | None = None