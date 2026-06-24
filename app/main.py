from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.config import get_settings
from app.core.logger import get_logger, stop_logger
from app.db.init_db import init_postgres_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger = get_logger("app.main")
    settings = get_settings()
    logger.info(f"Starting Application {settings.PROJECT_NAME}...")
    try:
        if settings.ENVIRONMENT == "development":
            await init_postgres_db()
        yield
    finally:
        stop_logger()

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.PROJECT_VERSION,
        lifespan=lifespan,
    )
    return app