from collections.abc import Sequence
from uuid import UUID

from app.core.logger import get_logger
from app.db.models import Project
from app.domains.projects.exceptions import ProjectNotFoundError
from app.domains.projects.repository import ProjectRepository
from app.domains.projects.schemas import CreateProjectDTO, UpdateProjectDTO

logger = get_logger("app.projects.service")


class ProjectService:
    def __init__(self, repo: ProjectRepository):
        self.repo = repo

    async def create_project(self, owner_id: UUID, dto: CreateProjectDTO):
        return await self.repo.create(owner_id, dto)

    async def list_user_projects(self, user_id: UUID) -> Sequence[Project]:
        return await self.repo.list_for_user(user_id)

    async def get_board(self, project_id: int) -> Project:
        project = await self.repo.get_board(project_id)
        if project is None:
            raise ProjectNotFoundError(project_id)
        return project

    async def get_project(self, project_id: int) -> Project:
        project = await self.repo.get(project_id)
        if project is None:
            raise ProjectNotFoundError(project_id)
        return project

    async def update_project(self, project: Project, dto: UpdateProjectDTO) -> Project:
        changes = dto.model_dump(exclude_unset=True)
        if changes.get("name") is None:
            changes.pop("name", None)

        project = await self.repo.update(project, changes)
        logger.info("Project updated", extra={"project_id": project.id})
        return project

    async def delete_project(self, project: Project) -> None:
        project_id = project.id
        await self.repo.delete(project)
        logger.info("Project deleted", extra={"project_id": project_id})
