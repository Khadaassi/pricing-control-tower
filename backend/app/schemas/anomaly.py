from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class BusinessAnomalyRead(BaseModel):
    anomaly_type: str
    severity: str
    message: str

    promotion_id: int
    product_id: int
    store_id: int | None = None

    sales_count: int
    total_quantity: int
    total_revenue: Decimal
    threshold: Decimal

    model_config = ConfigDict(from_attributes=True)