from fastapi import APIRouter

from .routes.analytics_sales import router as analytics_sales_router
from .routes.anomalies import router as anomalies_router
from .routes.countries import router as countries_router
from .routes.kpis import router as kpis_router
from .routes.me import router as me_router
from .routes.metrics import router as metrics_router
from .routes.price_change_requests import router as price_change_requests_router
from .routes.price_history import router as price_history_router
from .routes.prices import router as prices_router
from .routes.product_families import router as product_families_router
from .routes.products import router as products_router
from .routes.promotions import router as promotions_router
from .routes.sales import router as sales_router
from .routes.stores import router as stores_router
from .routes.technical import router as technical_router

api_router = APIRouter()

api_router.include_router(technical_router)
api_router.include_router(metrics_router)
api_router.include_router(analytics_sales_router)
api_router.include_router(countries_router)
api_router.include_router(stores_router)
api_router.include_router(product_families_router)
api_router.include_router(products_router)
api_router.include_router(prices_router)
api_router.include_router(me_router)
api_router.include_router(promotions_router)
api_router.include_router(sales_router)
api_router.include_router(kpis_router)
api_router.include_router(anomalies_router)
api_router.include_router(price_change_requests_router)
api_router.include_router(price_history_router)