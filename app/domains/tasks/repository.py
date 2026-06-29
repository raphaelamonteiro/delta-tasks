from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Notification,
    NotificationType,
    ProjectMember,
    Stage,
    Task,
    TaskHistory,
)


class TaskRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, task_id: int) -> Task | None:
        return await self.db.get(Task, task_id)

    async def get_stages(self, stage_ids: Iterable[int]) -> dict[int, Stage]:
        result = await self.db.execute(select(Stage).where(Stage.id.in_(stage_ids)))
        return {stage.id: stage for stage in result.scalars()}

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
                type=NotificationType.ASSIGNMENT,
            )
        )
        await self.db.commit()
        task.responsible_id = responsible_id
        return True

    async def move_to_stage(
        self, task: Task, source: Stage, dest: Stage, author_id: UUID
    ) -> Task:
        """Move a tarefa para ``dest``, registra o histórico e notifica o responsável.

        A nova posição (fim da coluna de destino) é calculada por subconsulta dentro do
        próprio ``UPDATE``; o registro de histórico (RN-007) e a notificação (RN-008)
        entram no mesmo commit, mantendo a operação atômica.
        """
        next_position = (
            select(func.coalesce(func.max(Task.position), -1) + 1)
            .where(Task.stage_id == dest.id)
            .scalar_subquery()
        )
        result = await self.db.execute(
            update(Task)
            .where(Task.id == task.id)
            .values(stage_id=dest.id, position=next_position)
            .returning(Task.position)
            .execution_options(synchronize_session=False)
        )
        new_position = result.scalar_one()

        self.db.add(
            TaskHistory(
                task_id=task.id,
                from_stage_id=source.id,
                to_stage_id=dest.id,
                from_stage_name=source.name,
                to_stage_name=dest.name,
                author_id=author_id,
            )
        )
        if task.responsible_id is not None and task.responsible_id != author_id:
            self.db.add(
                Notification(
                    recipient_id=task.responsible_id,
                    task_id=task.id,
                    type=NotificationType.COLUMN_CHANGE,
                )
            )
        await self.db.commit()
        task.stage_id = dest.id
        task.position = new_position
        return task
