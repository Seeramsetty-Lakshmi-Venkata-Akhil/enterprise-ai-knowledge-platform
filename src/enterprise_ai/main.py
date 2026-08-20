import logging

from fastapi import FastAPI

from enterprise_ai.api.organizations import router as organizations_router
from enterprise_ai.api.system import router as system_router
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

    app.include_router(system_router)
    app.include_router(organizations_router)
    return app


app = create_app()
