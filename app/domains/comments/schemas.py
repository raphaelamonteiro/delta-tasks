from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field

from app.core.schemas import BaseDTO
from app.db.models import Comment


class CreateCommentDTO(BaseDTO):
    body: str = Field(min_length=1, max_length=2000)


class CommentResponse(BaseDTO):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    project_id: int
    author_id: UUID
    body: str
    created_at: datetime