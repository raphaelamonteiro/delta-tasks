from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field

from app.core.schemas import BaseDTO
from app.db.models import Project, ProjectMember, ProjectRole, Stage

# Papéis que o dono pode atribuir a um membro (o papel DONO é exclusivo do criador).
AssignableRole = Literal[ProjectRole.MEMBER, ProjectRole.OBSERVER]


class CreateProjectDTO(BaseDTO):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)


class UpdateProjectDTO(BaseDTO):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)


class AddMemberDTO(BaseDTO):
    user_id: UUID
    role: AssignableRole = ProjectRole.MEMBER


class UpdateMemberRoleDTO(BaseDTO):
    role: AssignableRole


class ProjectMemberResponse(BaseDTO):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    name: str
    email: str
    role: ProjectRole

    @classmethod
    def from_member(cls, member: ProjectMember) -> "ProjectMemberResponse":
        return cls(
            user_id=member.user_id,
            name=member.user.name,
            email=member.user.email,
            role=member.role,
        )


class TaskCardResponse(BaseDTO):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    responsible_id: UUID | None
    due_date: date | None
    position: int


class BoardColumnResponse(BaseDTO):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    position: int
    tasks: list[TaskCardResponse]

    @classmethod
    def from_stage(cls, stage: Stage) -> "BoardColumnResponse":
        return cls(
            id=stage.id,
            name=stage.name,
            position=stage.position,
            tasks=[TaskCardResponse.model_validate(task) for task in stage.tasks],
        )


class ProjectSummaryResponse(BaseDTO):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None
    owner_id: UUID
    created_at: datetime
    updated_at: datetime


class ProjectBoardResponse(BaseDTO):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None
    owner_id: UUID
    created_at: datetime
    updated_at: datetime
    columns: list[BoardColumnResponse]

    @classmethod
    def from_project(cls, project: Project) -> "ProjectBoardResponse":
        return cls(
            id=project.id,
            name=project.name,
            description=project.description,
            owner_id=project.owner_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
            columns=[BoardColumnResponse.from_stage(stage) for stage in project.stages],
        )
