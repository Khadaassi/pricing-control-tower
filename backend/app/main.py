from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(
        title="Pricing Control Tower API",
        version="0.1.0",
    )

    @app.get("/")
    def root():
        return {"message": "Pricing Control Tower API"}

    return app


app = create_app()