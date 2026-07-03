from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logger import get_logger
from app.db.models import ProjectRole, Task
from app.domains.auth.dependencies import CurrentUserDep, get_current_user
from app.domains.auth.principal import CurrentUser
from app.domains.tasks.dependencies import TaskServiceDep
from app.domains.tasks.exceptions import (ResponsibleNotMemberError,
    StageNotInProjectError,
    TaskNotFoundError)
from app.domains.tasks.schemas import (CreateTaskDTO, AssignResponsibleDTO, MoveTaskDTO, TaskHistoryResponse, TaskResponse, UpdateTaskDTO)
from app.domains.tasks.swagger_utils import (create_task_swagger, assign_responsible_swagger, get_task_history_swagger, move_task_swagger, update_task_swagger, delete_task_swagger)

logger = get_logger("app.tasks.router")

_WRITE_ROLES = frozenset({ProjectRole.OWNER, ProjectRole.MEMBER})

tasks_router = APIRouter(prefix="/tasks", tags=["Tasks"], dependencies=[Depends(get_current_user)])


def _require_project_write_access(project_id: int, user: CurrentUser) -> None:
    if user.role_in(project_id) not in _WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify tasks in this project.",
        )


def _require_write_access(task: Task, user: CurrentUser) -> None:
    _require_project_write_access(task.project_id, user)


def _require_read_access(task: Task, user: CurrentUser) -> None:
    # RN-003: qualquer membro do projeto (ou admin global) pode visualizar.
    if not (user.is_admin or user.is_member(task.project_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project.")

@tasks_router.post("", **create_task_swagger)
async def create_task( dto: CreateTaskDTO,
    user: CurrentUserDep,
    service: TaskServiceDep) -> TaskResponse:
    _require_project_write_access(dto.project_id, user)
    task = await service.create_task(user.id, dto)
    return TaskResponse.model_validate(task)

@tasks_router.get("/{task_id}/history", **get_task_history_swagger)
async def get_task_history( task_id: int,
    user: CurrentUserDep,
    service: TaskServiceDep) -> list[TaskHistoryResponse]:
    try:
        task = await service.get_task(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.") from exc

    _require_read_access(task, user)
    history = await service.list_history(task)
    return [TaskHistoryResponse.from_history(record) for record in history]


@tasks_router.patch("/{task_id}", **update_task_swagger)
async def update_task( task_id: int,
    dto: UpdateTaskDTO,
    user: CurrentUserDep,
    service: TaskServiceDep) -> TaskResponse:
    try:
        task = await service.get_task(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found." ) from exc

    _require_write_access(task, user)
    task = await service.update_task(task, dto)
    return TaskResponse.model_validate(task)


@tasks_router.patch("/{task_id}/responsible", **assign_responsible_swagger)
async def assign_responsible(task_id: int, dto: AssignResponsibleDTO, user: CurrentUserDep, service: TaskServiceDep) -> TaskResponse:
    try:
        task = await service.get_task(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.") from exc

    _require_write_access(task, user)

    try:
        task = await service.assign_responsible(task, dto.responsible_id)
    except ResponsibleNotMemberError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The assigned user is not a member of the project.") from exc

    return TaskResponse.model_validate(task)


@tasks_router.patch("/{task_id}/stage", **move_task_swagger)
async def move_task(
    task_id: int,
    dto: MoveTaskDTO,
    user: CurrentUserDep,
    service: TaskServiceDep) -> TaskResponse:
    try:
        task = await service.get_task(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.") from exc

    _require_write_access(task, user)

    try:
        task = await service.move_task(task, dto.stage_id, user.id)
    except StageNotInProjectError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The destination column does not belong to the task's project.") from exc

    return TaskResponse.model_validate(task)


@tasks_router.delete("/{task_id}", **delete_task_swagger)
async def delete_task(
    task_id: int,
    user: CurrentUserDep,
    service: TaskServiceDep) -> None:
    try:
        task = await service.get_task(task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",) from exc
    
    _require_write_access(task, user)
    await service.delete_task(task)
