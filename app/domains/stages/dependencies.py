from typing import Annotated
from fastapi import Depends

from app.db.dependencies import PgSessionDep
from app.domains.stages.repository import StageRepository
from app.domains.stages.service import StageService


def get_stage_repository(db: PgSessionDep) -> StageRepository:
    return StageRepository(db)

StageRepositoryDep = Annotated[StageRepository, Depends(get_stage_repository)]


def get_stage_service(repo: StageRepositoryDep) -> StageService:
    return StageService(repo)

StageServiceDep = Annotated[StageService, Depends(get_stage_service)]