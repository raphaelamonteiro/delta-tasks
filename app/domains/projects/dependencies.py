from typing import Annotated

from fastapi import Depends

from app.db.dependencies import PgSessionDep
from app.domains.projects.repository import ProjectRepository
from app.domains.projects.service import ProjectService


def get_project_repository(db: PgSessionDep) -> ProjectRepository:
    return ProjectRepository(db)


ProjectRepositoryDep = Annotated[ProjectRepository, Depends(get_project_repository)]


def get_project_service(repo: ProjectRepositoryDep) -> ProjectService:
    return ProjectService(repo=repo)


ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
