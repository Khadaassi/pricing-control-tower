from fastapi import FastAPI

from .api.routes.chat import router as chat_router
from .api.routes.health import router as health_router
from .api.routes.metrics import router as metrics_router
from .core.config import settings
from .middleware.metrics_middleware import PrometheusMetricsMiddleware


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
    )

    app.add_middleware(PrometheusMetricsMiddleware)

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "message": settings.app_name,
            "docs": "/docs",
            "health": "/chat/health",
            "chat": "/chat",
            "metrics": "/metrics",
        }

    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(metrics_router)

    return app


app = create_app()