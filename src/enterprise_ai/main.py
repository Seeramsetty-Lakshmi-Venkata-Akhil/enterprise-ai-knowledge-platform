from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(
        title="Enterprise AI Knowledge Platform",
        version="0.1.0",
    )

    @app.get("/health", tags=["System"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy"}

    return app


app = create_app()