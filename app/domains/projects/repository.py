from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Project, ProjectMember, ProjectRole, Stage, User
from app.domains.projects.schemas import CreateProjectDTO

_BOARD_OPTIONS = selectinload(Project.stages).selectinload(Stage.tasks)

DEFAULT_COLUMNS = ("Pendente", "Em Progresso", "Em Revisão", "Concluído")

class ProjectRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self, owner_id: UUID, dto: CreateProjectDTO, column_names: Sequence[str] = DEFAULT_COLUMNS) -> Project:
        project = Project(name=dto.name, description=dto.description, owner_id=owner_id)
        project.members.append(ProjectMember(user_id=owner_id, role=ProjectRole.OWNER))
        project.stages = [Stage(name=name, position=position) for position, name in enumerate(column_names)]

        self.db.add(project)
        await self.db.commit()

        result = await self.db.execute(
            select(Project).where(Project.id == project.id).options(_BOARD_OPTIONS))
        return result.scalars().one()

    async def list_for_user(self, user_id: UUID) -> Sequence[Project]:
        result = await self.db.execute(
            select(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(ProjectMember.user_id == user_id)
            .order_by(Project.created_at))
        return result.scalars().all()

    async def get_board(self, project_id: int) -> Project | None:
        result = await self.db.execute(
            select(Project).where(Project.id == project_id).options(_BOARD_OPTIONS)
        )
        return result.scalars().first()

    async def get(self, project_id: int) -> Project | None:
        return await self.db.get(Project, project_id)

    async def update(self, project: Project, changes: dict[str, Any]) -> Project:
        for field, value in changes.items():
            setattr(project, field, value)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        await self.db.delete(project)
        await self.db.commit()

    async def user_exists(self, user_id: UUID) -> bool:
        result = await self.db.execute(select(User.id).where(User.id == user_id))
        return result.scalar_one_or_none() is not None

    async def list_members(self, project_id: int) -> Sequence[ProjectMember]:
        result = await self.db.execute(
            select(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .options(selectinload(ProjectMember.user))
            .order_by(ProjectMember.created_at)
        )
        return result.scalars().all()

    async def get_member(self, project_id: int, user_id: UUID) -> ProjectMember | None:
        result = await self.db.execute(
            select(ProjectMember)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
            .options(selectinload(ProjectMember.user))
        )
        return result.scalar_one_or_none()

    async def add_member(
        self, project_id: int, user_id: UUID, role: ProjectRole
    ) -> ProjectMember:
        member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
        self.db.add(member)
        await self.db.commit()
        loaded = await self.get_member(project_id, user_id)
        assert loaded is not None
        return loaded

    async def update_member_role(
        self, member: ProjectMember, role: ProjectRole
    ) -> ProjectMember:
        member.role = role
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def remove_member(self, member: ProjectMember) -> None:
        await self.db.delete(member)
        await self.db.commit()
