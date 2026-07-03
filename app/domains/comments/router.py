from fastapi import APIRouter, Depends, HTTPException, status
from app.core.logger import get_logger
from app.db.models import Task
from app.domains.auth.dependencies import CurrentUserDep, get_current_user
from app.domains.auth.principal import CurrentUser
from app.domains.tasks.dependencies import TaskServiceDep
from app.domains.tasks.exceptions import TaskNotFoundError
from app.domains.comments.dependencies import CommentServiceDep

from app.domains.comments.schemas import (
    CreateCommentDTO,
    CommentResponse,
)

logger = get_logger("app.comments.router")

comments_router = APIRouter(
    prefix="/tasks",
    tags=["Comments"],
    dependencies=[Depends(get_current_user)],
)


# -------------------------
# Permission helper
# -------------------------
def _require_access(task: Task, user: CurrentUser) -> None:
    if not (user.is_admin or user.is_member(task.project_id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project.",
        )


# -------------------------
# Create comment
# -------------------------
@comments_router.post("/{task_id}/comments")
async def create_comment(
    task_id: int,
    dto: CreateCommentDTO,
    user: CurrentUserDep,
    task_service: TaskServiceDep,
    comment_service: CommentServiceDep,
) -> CommentResponse:
    try:
        task = await task_service.get_task(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        ) from exc

    _require_access(task, user)

    comment = await comment_service.create_comment(
        task=task,
        author_id=user.id,
        dto=dto,
    )

    return CommentResponse.from_comment(comment)


# -------------------------
# List comments
# -------------------------
@comments_router.get("/{task_id}/comments")
async def list_comments(
    task_id: int,
    user: CurrentUserDep,
    task_service: TaskServiceDep,
    comment_service: CommentServiceDep,
) -> list[CommentResponse]:
    try:
        task = await task_service.get_task(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        ) from exc

    _require_access(task, user)

    comments = await comment_service.list_comments(task)

    return [
        CommentResponse.from_comment(comment)
        for comment in comments
    ]