from datetime import date, datetime
from uuid import UUID
from pydantic import ConfigDict, Field
from app.core.schemas import BaseDTO
from app.db.models import TaskHistory

class CreateTaskDTO(BaseDTO):
    title: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    due_date: date | None = None
    position: int
    project_id: UUID
    stage_id: int
    responsible_id: UUID


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


class TaskHistoryResponse(BaseDTO):
    id: int
    from_stage_id: int | None
    to_stage_id: int | None
    from_stage_name: str
    to_stage_name: str
    author_id: UUID
    author_name: str
    created_at: datetime

    @classmethod
    def from_history(cls, history: TaskHistory) -> "TaskHistoryResponse":
        return cls(
            id=history.id,
            from_stage_id=history.from_stage_id,
            to_stage_id=history.to_stage_id,
            from_stage_name=history.from_stage_name,
            to_stage_name=history.to_stage_name,
            author_id=history.author_id,
            author_name=history.author.name,
            created_at=history.created_at,
        )
