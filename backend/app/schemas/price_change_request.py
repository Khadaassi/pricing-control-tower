from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PriceChangeRequestCreate(BaseModel):
    product_id: int = Field(gt=0)
    country_id: int = Field(gt=0)
    store_id: int | None = Field(default=None, gt=0)

    requested_price_amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    justification: str = Field(min_length=1)
    requested_effective_date: date

    @field_validator("justification")
    @classmethod
    def validate_justification_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("justification must not be empty")
        return value.strip()


class PriceChangeRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    product_id: int
    country_id: int
    store_id: int | None
    current_price_id: int

    old_price_amount: Decimal
    requested_price_amount: Decimal

    status: str
    justification: str
    requested_effective_date: date

    requested_by_user_id: int
    rejection_reason: str | None = None
    rejected_by_user_id: int | None = None
    rejected_at: datetime | None = None

    created_at: datetime
    updated_at: datetime


class PriceChangeRequestReject(BaseModel):
    reason: str = Field(min_length=1)

    @field_validator("reason")
    @classmethod
    def validate_reason_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("reason must not be empty")
        return value.strip()