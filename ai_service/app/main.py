from fastapi import FastAPI

from .api.routes.health import router as health_router
from .core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
    )

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "message": settings.app_name,
            "docs": "/docs",
            "health": "/health",
        }

    app.include_router(health_router)
    return app


app = create_app()
