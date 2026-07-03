from collections.abc import Sequence
from uuid import UUID

from app.core.logger import get_logger
from app.db.models import Project, ProjectMember, ProjectRole
from app.domains.projects.exceptions import (
    DuplicateMemberError,
    MemberUserNotFoundError,
    OwnerMembershipError,
    ProjectMemberNotFoundError,
    ProjectNotFoundError,
)
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

    async def list_members(self, project_id: int) -> Sequence[ProjectMember]:
        return await self.repo.list_members(project_id)

    async def add_member(
        self, project_id: int, user_id: UUID, role: ProjectRole
    ) -> ProjectMember:
        if not await self.repo.user_exists(user_id):
            raise MemberUserNotFoundError(user_id)
        if await self.repo.get_member(project_id, user_id) is not None:
            raise DuplicateMemberError(project_id, user_id)

        member = await self.repo.add_member(project_id, user_id, role)
        logger.info(
            "Project member added",
            extra={"project_id": project_id, "user_id": str(user_id), "role": role.value},
        )
        return member

    async def update_member_role(
        self, project_id: int, user_id: UUID, role: ProjectRole
    ) -> ProjectMember:
        member = await self._get_manageable_member(project_id, user_id)
        member = await self.repo.update_member_role(member, role)
        logger.info(
            "Project member role updated",
            extra={"project_id": project_id, "user_id": str(user_id), "role": role.value},
        )
        return member

    async def remove_member(self, project_id: int, user_id: UUID) -> None:
        member = await self._get_manageable_member(project_id, user_id)
        await self.repo.remove_member(member)
        logger.info(
            "Project member removed",
            extra={"project_id": project_id, "user_id": str(user_id)},
        )

    async def _get_manageable_member(self, project_id: int, user_id: UUID) -> ProjectMember:
        member = await self.repo.get_member(project_id, user_id)
        if member is None:
            raise ProjectMemberNotFoundError(project_id, user_id)
        # RN-009: o vínculo do dono é imutável por esta via.
        if member.role is ProjectRole.OWNER:
            raise OwnerMembershipError(project_id, user_id)
        return member
