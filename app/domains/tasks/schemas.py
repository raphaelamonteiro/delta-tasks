from datetime import date
from uuid import UUID

from pydantic import ConfigDict

from app.core.schemas import BaseDTO


class AssignResponsibleDTO(BaseDTO):
    responsible_id: UUID


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
