from fastapi import APIRouter

from .routes.anomalies import router as anomalies_router
from .routes.kpis import router as kpis_router
from .routes.prices import router as prices_router
from .routes.products import router as products_router
from .routes.promotions import router as promotions_router
from .routes.sales import router as sales_router
from .routes.technical import router as technical_router

api_router = APIRouter()

api_router.include_router(technical_router)
api_router.include_router(products_router)
api_router.include_router(prices_router)
api_router.include_router(promotions_router)
api_router.include_router(sales_router)
api_router.include_router(kpis_router)
api_router.include_router(anomalies_router)