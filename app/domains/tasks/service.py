from uuid import UUID

from app.core.logger import get_logger
from app.db.models import Task
from app.domains.tasks.exceptions import ResponsibleNotMemberError, TaskNotFoundError
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
        # Reatribuir o mesmo responsável é um no-op: nada muda e não há nova notificação.
        if task.responsible_id == responsible_id:
            return task

        if not await self.repo.assign_responsible(task, responsible_id):
            raise ResponsibleNotMemberError(responsible_id, task.project_id)

        logger.info(
            "Task responsible assigned",
            extra={"task_id": task.id, "responsible_id": str(responsible_id)},
        )
        return task
