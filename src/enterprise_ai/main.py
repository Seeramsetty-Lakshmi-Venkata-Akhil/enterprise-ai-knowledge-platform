import logging

from fastapi import FastAPI

from enterprise_ai.core.config import get_settings
from enterprise_ai.core.logging import configure_logging

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    logger.info(
        "Starting application",
        extra={"app_env": settings.app_env},
    )

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
    )

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "healthy"}

    return app


app = create_app()
