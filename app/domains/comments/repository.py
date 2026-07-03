from collections.abc import Iterable, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Comment,
    Notification,
    NotificationType,
    Project,
)
from app.domains.comments.schemas import CreateCommentDTO


class CommentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        task_id: int,
        author_id: UUID,
        dto: CreateCommentDTO,
        recipients: Iterable[UUID],
    ) -> Comment:
        comment = Comment(
            task_id=task_id,
            author_id=author_id,
            body=dto.body,
        )

        self.db.add(comment)

        for recipient_id in recipients:
            self.db.add(
                Notification(
                    recipient_id=recipient_id,
                    task_id=task_id,
                    type=NotificationType.NEW_COMMENT,
                )
            )

        await self.db.commit()
        await self.db.refresh(comment)

        result = await self.db.execute(
            select(Comment)
            .where(Comment.id == comment.id)
            .options(selectinload(Comment.task))
        )

        return result.scalars().one()

    async def list_by_task(self, task_id: int) -> Sequence[Comment]:
        result = await self.db.execute(
            select(Comment)
            .where(Comment.task_id == task_id)
            .options(selectinload(Comment.task))
            .order_by(Comment.created_at)
        )

        return result.scalars().all()

    async def get_project_owner_id(self, project_id: int) -> UUID:
        result = await self.db.execute(
            select(Project.owner_id).where(Project.id == project_id)
        )
        return result.scalar_one()