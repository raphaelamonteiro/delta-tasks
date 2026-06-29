from datetime import date
from uuid import UUID

from pydantic import ConfigDict, Field

from app.core.schemas import BaseDTO


class UpdateTaskDTO(BaseDTO):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    due_date: date | None = Field(default=None)


class AssignResponsibleDTO(BaseDTO):
    responsible_id: UUID


class MoveTaskDTO(BaseDTO):
    stage_id: int


class TaskResponse(BaseDTO):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    stage_id: int
    title: str
    description: str | None
    responsible_id: UUID | None
    due_date: date | None
    position: int
