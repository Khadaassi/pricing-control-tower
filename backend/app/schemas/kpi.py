from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SalesKpiRead(BaseModel):
    total_sales_count: int
    total_quantity: int
    total_revenue: Decimal
    promo_sales_count: int
    promo_revenue: Decimal
    promo_sales_share: Decimal
    average_order_value: Decimal

    model_config = ConfigDict(from_attributes=True)