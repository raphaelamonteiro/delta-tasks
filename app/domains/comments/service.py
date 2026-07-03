from app.core.logger import get_logger
from collections.abc import Sequence
from app.db.models import Comment, Task
from app.domains.comments.repository import CommentRepository
from app.domains.comments.schemas import CreateCommentDTO
from uuid import UUID

logger = get_logger("app.comments.service")

class CommentService:
    def __init__(self, repo: CommentRepository):
        self.repo = repo

    async def create_comment(self, task: Task, author_id: UUID, dto: CreateCommentDTO) -> Comment:
        recipients = await self._comment_recipients(task, author_id)
        comment = await self.repo.create(
            task_id=task.id,
            author_id=author_id,
            dto=dto,
            recipients=recipients
        )

        logger.info(
            "Comment created",
            extra={
                "task_id": task.id,
                "author_id": str(author_id),
                "comment_id": comment.id,
            },
        )

        return comment

    async def list_comments(self, task: Task) -> Sequence[Comment]:
        return await self.repo.list_by_task(task.id)

    async def _comment_recipients(
        self,
        task: Task,
        author_id: UUID,
    ) -> set[UUID]:
        recipients = {
            await self.repo.get_project_owner_id(task.project_id)
        }

        if task.responsible_id is not None:
            recipients.add(task.responsible_id)

        recipients.discard(author_id)

        return recipients

    