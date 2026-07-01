from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Project, ProjectMember, ProjectRole, Stage
from app.domains.projects.schemas import CreateProjectDTO

_BOARD_OPTIONS = selectinload(Project.stages).selectinload(Stage.tasks)

class ProjectRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self, owner_id: UUID, dto: CreateProjectDTO, column_names: Sequence[str]
    ) -> Project:
        project = Project(name=dto.name, description=dto.description, owner_id=owner_id)
        project.members.append(ProjectMember(user_id=owner_id, role=ProjectRole.OWNER))
        project.stages = [
            Stage(name=name, position=position) for position, name in enumerate(column_names)
        ]

        self.db.add(project)
        await self.db.commit()

        result = await self.db.execute(
            select(Project).where(Project.id == project.id).options(_BOARD_OPTIONS)
        )
        return result.scalars().one()

    async def list_for_user(self, user_id: UUID) -> Sequence[Project]:
        result = await self.db.execute(
            select(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(ProjectMember.user_id == user_id)
            .order_by(Project.created_at)
        )
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
