from fastapi import FastAPI

from .api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Pricing Control Tower API",
        version="0.1.0",
    )

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
