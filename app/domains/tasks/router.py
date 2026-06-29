from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logger import get_logger
from app.db.models import ProjectRole, Task
from app.domains.auth.dependencies import CurrentUserDep, get_current_user
from app.domains.auth.principal import CurrentUser
from app.domains.tasks.dependencies import TaskServiceDep
from app.domains.tasks.exceptions import ResponsibleNotMemberError, TaskNotFoundError
from app.domains.tasks.schemas import AssignResponsibleDTO, TaskResponse
from app.domains.tasks.swagger_utils import assign_responsible_swagger

logger = get_logger("app.tasks.router")

# RN-003: apenas membros com papel de escrita podem alterar o responsável.
# Observadores (e não membros) são bloqueados.
_WRITE_ROLES = frozenset({ProjectRole.OWNER, ProjectRole.MEMBER})

tasks_router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
    dependencies=[Depends(get_current_user)],
)


def _require_can_assign(task: Task, user: CurrentUser) -> None:
    if user.role_in(task.project_id) not in _WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to change the responsible of this task.",
        )


@tasks_router.patch("/{task_id}/responsible", **assign_responsible_swagger)
async def assign_responsible(
    task_id: int,
    dto: AssignResponsibleDTO,
    user: CurrentUserDep,
    service: TaskServiceDep,
) -> TaskResponse:
    try:
        task = await service.get_task(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        ) from exc

    _require_can_assign(task, user)

    try:
        task = await service.assign_responsible(task, dto.responsible_id)
    except ResponsibleNotMemberError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The assigned user is not a member of the project.",
        ) from exc

    return TaskResponse.model_validate(task)
