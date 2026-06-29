from uuid import UUID

from app.core.logger import get_logger
from app.db.models import Task
from app.domains.tasks.exceptions import (
    ResponsibleNotMemberError,
    StageNotInProjectError,
    TaskNotFoundError,
)
from app.domains.tasks.repository import TaskRepository

logger = get_logger("app.tasks.service")


class TaskService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo

    async def get_task(self, task_id: int) -> Task:
        task = await self.repo.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    async def assign_responsible(self, task: Task, responsible_id: UUID) -> Task:
        if task.responsible_id == responsible_id:
            return task

        if not await self.repo.assign_responsible(task, responsible_id):
            raise ResponsibleNotMemberError(responsible_id, task.project_id)

        logger.info(
            "Task responsible assigned",
            extra={"task_id": task.id, "responsible_id": str(responsible_id)},
        )
        return task

    async def move_task(self, task: Task, dest_stage_id: int, author_id: UUID) -> Task:
        stages = await self.repo.get_stages({task.stage_id, dest_stage_id})

        dest = stages.get(dest_stage_id)
        if dest is None or dest.project_id != task.project_id:
            raise StageNotInProjectError(dest_stage_id, task.project_id)

        if task.stage_id == dest_stage_id:
            return task

        source = stages[task.stage_id]
        task = await self.repo.move_to_stage(task, source, dest, author_id)
        logger.info(
            "Task moved",
            extra={"task_id": task.id, "from_stage_id": source.id, "to_stage_id": dest.id},
        )
        return task
