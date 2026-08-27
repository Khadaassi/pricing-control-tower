from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.router import api_router
from .config import is_gdpr_retention_enabled
from .core.logging_config import configure_logging
from .core.scheduler import shutdown_scheduler, start_scheduler
from .middleware.logging_middleware import StructuredLoggingMiddleware
from .middleware.metrics_middleware import PrometheusMetricsMiddleware


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    # GDPR retention job (C4) — see app/core/scheduler.py. Disabled via
    # GDPR_RETENTION_ENABLED=false in the test environment, since TestClient(app)
    # is normally used without a `with` block in this codebase, which never
    # triggers this lifespan at all.
    if is_gdpr_retention_enabled():
        start_scheduler()

    yield

    if is_gdpr_retention_enabled():
        shutdown_scheduler()


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="Pricing Control Tower API",
        version="0.1.0",
        lifespan=_lifespan,
    )

    app.add_middleware(StructuredLoggingMiddleware)
    app.add_middleware(PrometheusMetricsMiddleware)

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