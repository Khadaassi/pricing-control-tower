from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class BusinessAnomalyRead(BaseModel):
    anomaly_type: str
    severity: str
    message: str

    promotion_id: int | None = None
    product_id: int
    product_family_name: str | None = None
    store_id: int | None = None

    promotion_active: bool = False

    sales_count: int = 0
    total_quantity: int = 0
    total_revenue: Decimal = Decimal("0.00")
    threshold: Decimal

    model_config = ConfigDict(from_attributes=True)
