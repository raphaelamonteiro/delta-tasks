from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.logger import get_logger, stop_logger
from app.db.init_db import init_postgres_db
from app.domains.auth.router import auth_router
from app.domains.projects.router import projects_router
from app.domains.tasks.router import tasks_router
from app.domains.users.router import users_router
from app.domains.stages.router import stages_router
from app.domains.comments.router import comments_router

import asyncio
from app.core.notifications.worker import NotificationWorker
from app.core.notifications.email_service import EmailService
from app.db.engine import async_session

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger = get_logger("app.main")
    settings = get_settings()
    logger.info(f"Starting Application {settings.PROJECT_NAME}...")
    
    worker = NotificationWorker(
        email_service=EmailService(),
        interval_seconds=10,
    )

    worker_task: asyncio.Task | None = None
    
    try:
        if settings.ENVIRONMENT == "development":
            await init_postgres_db()
        worker_task = asyncio.create_task(worker.start())
        yield
    finally:
        logger.info("Shutting down aplication...")
        worker.running = False
        if worker_task:
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass
        stop_logger()


async def validation_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    errors: Sequence[Any] = (exc.errors() if isinstance(exc, RequestValidationError) else [])
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": jsonable_encoder(errors)})

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.PROJECT_VERSION, 
        lifespan=lifespan)
    
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(projects_router)
    app.include_router(tasks_router)
    app.include_router(stages_router)
    app.include_router(comments_router)
    return app