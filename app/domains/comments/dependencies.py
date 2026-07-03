from typing import Annotated

from fastapi import Depends

from app.db.dependencies import PgSessionDep
from app.domains.comments.repository import CommentRepository
from app.domains.comments.service import CommentService


def get_comment_repository(db: PgSessionDep) -> CommentRepository:
    return CommentRepository(db)


CommentRepositoryDep = Annotated[
    CommentRepository,
    Depends(get_comment_repository),
]


def get_comment_service(repo: CommentRepositoryDep) -> CommentService:
    return CommentService(repo=repo)


CommentServiceDep = Annotated[
    CommentService,
    Depends(get_comment_service),
]