
from asyncio.log import logger
from collections.abc import Iterable, Sequence
from typing import Any
from uuid import UUID
from app.db.models import (Notification, NotificationType, Project, ProjectMember, Stage, Task, TaskHistory)
from app.domains.tasks.schemas import CreateTaskDTO
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

class TaskRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_task(self, project_id: int, responsible_id: UUID, dto: CreateTaskDTO) -> Task:
        task = await self.repo.create(project_id, responsible_id, dto)

        logger.info("Task created",
        extra={"task_id": task.id, "responsible_id": str(responsible_id)})
        return task

    async def create( self, project_id: int, responsible_id: UUID, dto: CreateTaskDTO ) -> Task:
        task = Task(title=dto.title, description=dto.description, project_id=project_id,
        stage_id=dto.stage_id, responsible_id=responsible_id, due_date=dto.due_date, position=dto.position)

        self.db.add(task)

        await self.db.commit()
        await self.db.refresh(task)
        return task


    async def get(self, task_id: int) -> Task | None:
        result = await self.db.execute(
            select(Task)
            .where(Task.id == task_id)
            .options( selectinload(Task.project),
            selectinload(Task.stage)))
        return result.scalar_one_or_none()

    async def get_stages(self, stage_ids: Iterable[int]) -> dict[int, Stage]:
        result = await self.db.execute(select(Stage).where(Stage.id.in_(stage_ids)))
        return {stage.id: stage for stage in result.scalars()}

    async def get_project_owner_id(self, project_id: int) -> UUID:
        result = await self.db.execute(
            select(Project.owner_id).where(Project.id == project_id)
        )
        return result.scalar_one()

    async def list_history(self, task_id: int) -> Sequence[TaskHistory]:
        result = await self.db.execute(
            select(TaskHistory)
            .where(TaskHistory.task_id == task_id)
            .options(selectinload(TaskHistory.author))
            .order_by(TaskHistory.created_at, TaskHistory.id)
        )
        return result.scalars().all()

    async def update(self, task: Task, changes: dict[str, Any]) -> Task:
        for field, value in changes.items():
            setattr(task, field, value)
        await self.db.commit()
        return task

    async def assign_responsible(self, task: Task, responsible_id: UUID) -> bool:
        """Atribui o responsável somente se ele for membro do projeto da tarefa.

        Retorna ``True`` se a atribuição foi aplicada; ``False`` se o usuário não é membro
        (nada é gravado).
        """
        is_member = (
            select(ProjectMember.id)
            .where(
                ProjectMember.project_id == task.project_id,
                ProjectMember.user_id == responsible_id,
            )
            .exists()
        )
        result = await self.db.execute(
            update(Task)
            .where(Task.id == task.id, is_member)
            .values(responsible_id=responsible_id)
            .returning(Task.id)
            .execution_options(synchronize_session=False)
        )
        if result.scalar_one_or_none() is None:
            return False

        self.db.add(
            Notification(
                recipient_id=responsible_id,
                task_id=task.id,
                type=NotificationType.ASSIGNMENT))
        await self.db.commit()
        task.responsible_id = responsible_id
        return True

    async def move_to_stage(self, task: Task, source: Stage, dest: Stage,
        author_id: UUID, recipients: Iterable[UUID]) -> Task:
        """Move a tarefa para ``dest``, registra o histórico e notifica ``recipients``.

        A nova posição (fim da coluna de destino) é calculada por subconsulta dentro do
        próprio ``UPDATE``; o registro de histórico (RN-007) e as notificações (RN-008)
        entram no mesmo commit, mantendo a operação atômica. A política de quem é
        notificado fica no serviço; aqui apenas persistimos o conjunto recebido.
        """
        next_position = (select(func.coalesce(func.max(Task.position), -1) + 1)
        .where(Task.stage_id == dest.id).scalar_subquery())
        result = await self.db.execute(update(Task).where(Task.id == task.id).values(stage_id=dest.id, position=next_position).returning(Task.position).execution_options(synchronize_session=False))
        new_position = result.scalar_one()

        self.db.add(TaskHistory(task_id=task.id,
                from_stage_id=source.id,
                to_stage_id=dest.id,
                from_stage_name=source.name,
                to_stage_name=dest.name, author_id=author_id))
        for recipient_id in recipients:
            self.db.add(Notification(recipient_id=recipient_id, task_id=task.id, type=NotificationType.COLUMN_CHANGE))
        await self.db.commit()
        task.stage_id = dest.id
        task.position = new_position
        return task
    
    async def delete(self, task: Task) -> None:
        await self.db.delete(task)
        await self.db.commit()
