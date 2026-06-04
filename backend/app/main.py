from fastapi import FastAPI

from .api.router import api_router
from .core.logging_config import configure_logging
from .middleware.logging_middleware import StructuredLoggingMiddleware


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="Pricing Control Tower API",
        version="0.1.0",
    )

    app.add_middleware(StructuredLoggingMiddleware)

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "message": "Pricing Control Tower API",
            "docs": "/docs",
            "health": "/health",
        }

    app.include_router(api_router)
    return app


app = create_app()