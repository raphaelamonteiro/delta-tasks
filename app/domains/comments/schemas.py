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

    @classmethod
    def from_comment(cls, comment: Comment) -> "CommentResponse":
        return cls(
            id=comment.id,
            task_id=comment.task_id,
            project_id=comment.task.project_id,
            author_id=comment.author_id,
            body=comment.body,
            created_at=comment.created_at,
        )