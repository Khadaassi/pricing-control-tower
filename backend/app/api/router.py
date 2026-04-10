from fastapi import APIRouter

from .routes.prices import router as prices_router
from .routes.products import router as products_router
from .routes.promotions import router as promotions_router
from .routes.technical import router as technical_router

api_router = APIRouter()

api_router.include_router(technical_router)
api_router.include_router(products_router)
api_router.include_router(prices_router)
api_router.include_router(promotions_router)
