from typing import Annotated
from fastapi import Depends
from app.db.dependencies import PgSessionDep
from app.domains.tasks.repository import TaskRepository
from app.domains.tasks.service import TaskService


def get_task_repository(db: PgSessionDep) -> TaskRepository:
    return TaskRepository(db)


TaskRepositoryDep = Annotated[TaskRepository, Depends(get_task_repository)]


def get_task_service(repo: TaskRepositoryDep) -> TaskService:
    return TaskService(repo=repo)


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
