from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Notification, NotificationType, ProjectMember, Task


class TaskRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, task_id: int) -> Task | None:
        return await self.db.get(Task, task_id)

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
