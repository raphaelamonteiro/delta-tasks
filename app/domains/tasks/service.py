from collections.abc import Sequence
from uuid import UUID
from app.core.logger import get_logger
from app.db.models import Task, TaskHistory
from app.domains.tasks.exceptions import (ResponsibleNotMemberError, StageNotInProjectError, TaskNotFoundError)
from app.domains.tasks.repository import TaskRepository
from app.domains.tasks.schemas import (CreateTaskDTO, UpdateTaskDTO)

logger = get_logger("app.tasks.service")

class TaskService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo

    async def create_task(self, responsible_id: UUID, dto: CreateTaskDTO) -> Task:
        stages = await self.repo.get_stages({dto.stage_id})
        stage = stages.get(dto.stage_id)
        if stage is None or stage.project_id != dto.project_id:
            raise StageNotInProjectError(dto.stage_id, dto.project_id)

        task = await self.repo.create(
            project_id=dto.project_id, responsible_id=responsible_id, dto=dto
        )
        logger.info(
            "Task created", extra={"task_id": task.id, "responsible_id": str(responsible_id)}
        )
        return task

    async def get_task(self, task_id: int) -> Task:
        task = await self.repo.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)      
        return task

    async def list_history(self, task: Task) -> Sequence[TaskHistory]:
        return await self.repo.list_history(task.id)

    async def update_task(self, task: Task, dto: UpdateTaskDTO) -> Task:
        changes = dto.model_dump(exclude_unset=True)
        # title é obrigatório no modelo: ignora tentativa de defini-lo como nulo.
        if changes.get("title") is None:
            changes.pop("title", None)

        task = await self.repo.update(task, changes)
        logger.info("Task updated", extra={"task_id": task.id})
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
        recipients = await self._move_recipients(task, author_id)
        task = await self.repo.move_to_stage(task, source, dest, author_id, recipients)
        logger.info(
            "Task moved",
            extra={"task_id": task.id, "from_stage_id": source.id, "to_stage_id": dest.id},
        )
        return task

    async def _move_recipients(self, task: Task, author_id: UUID) -> set[UUID]:
        # RN-008: notifica o responsável e o dono do projeto, exceto quem moveu a tarefa.
        recipients = {await self.repo.get_project_owner_id(task.project_id)}
        if task.responsible_id is not None:
            recipients.add(task.responsible_id)
        recipients.discard(author_id)
        return recipients

    async def delete_task(self, task: Task) -> None:
        task_id = task.id
        await self.repo.delete(task)
        logger.info("Task deleted", extra={"task_id": task_id})
