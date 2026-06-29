from datetime import date
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.db.models import Stage, Task, TaskHistory
from app.domains.tasks.exceptions import (
    ResponsibleNotMemberError,
    StageNotInProjectError,
    TaskNotFoundError,
)
from app.domains.tasks.schemas import UpdateTaskDTO
from app.domains.tasks.service import TaskService


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(repo: AsyncMock) -> TaskService:
    return TaskService(repo=repo)


async def test_get_task_returns_task(service: TaskService, repo: AsyncMock) -> None:
    task = Task(id=1, project_id=1, stage_id=1, title="T", position=0)
    repo.get.return_value = task

    assert await service.get_task(1) is task
    repo.get.assert_awaited_once_with(1)


async def test_get_task_raises_when_missing(service: TaskService, repo: AsyncMock) -> None:
    repo.get.return_value = None

    with pytest.raises(TaskNotFoundError):
        await service.get_task(999)


async def test_assign_responsible_to_member(service: TaskService, repo: AsyncMock) -> None:
    responsible_id = uuid4()
    task = Task(id=1, project_id=7, stage_id=1, title="T", position=0)
    repo.assign_responsible.return_value = True

    result = await service.assign_responsible(task, responsible_id)

    assert result is task
    repo.assign_responsible.assert_awaited_once_with(task, responsible_id)


async def test_assign_responsible_rejects_non_member(service: TaskService, repo: AsyncMock) -> None:
    responsible_id = uuid4()
    task = Task(id=1, project_id=7, stage_id=1, title="T", position=0)
    repo.assign_responsible.return_value = False

    with pytest.raises(ResponsibleNotMemberError):
        await service.assign_responsible(task, responsible_id)


async def test_reassigning_same_responsible_is_noop(service: TaskService, repo: AsyncMock) -> None:
    responsible_id = uuid4()
    task = Task(
        id=1, project_id=7, stage_id=1, title="T", position=0, responsible_id=responsible_id
    )

    result = await service.assign_responsible(task, responsible_id)

    assert result is task
    repo.assign_responsible.assert_not_awaited()


async def test_assign_substitutes_previous_responsible(
    service: TaskService, repo: AsyncMock
) -> None:
    previous = uuid4()
    new_responsible = uuid4()
    task = Task(id=1, project_id=7, stage_id=1, title="T", position=0, responsible_id=previous)
    repo.assign_responsible.return_value = True

    await service.assign_responsible(task, new_responsible)

    repo.assign_responsible.assert_awaited_once_with(task, new_responsible)


async def test_move_task_to_another_column(service: TaskService, repo: AsyncMock) -> None:
    author_id = uuid4()
    owner_id = uuid4()
    task = Task(id=1, project_id=7, stage_id=10, title="T", position=0)
    source = Stage(id=10, project_id=7, name="Pendente", position=0)
    dest = Stage(id=20, project_id=7, name="Em Progresso", position=1)
    repo.get_stages.return_value = {10: source, 20: dest}
    repo.get_project_owner_id.return_value = owner_id
    repo.move_to_stage.return_value = task

    result = await service.move_task(task, 20, author_id)

    assert result is task
    repo.get_stages.assert_awaited_once_with({10, 20})
    repo.move_to_stage.assert_awaited_once_with(task, source, dest, author_id, {owner_id})


async def test_move_task_notifies_owner_and_responsible(
    service: TaskService, repo: AsyncMock
) -> None:
    author_id, owner_id, responsible_id = uuid4(), uuid4(), uuid4()
    task = Task(
        id=1, project_id=7, stage_id=10, title="T", position=0, responsible_id=responsible_id
    )
    source = Stage(id=10, project_id=7, name="Pendente", position=0)
    dest = Stage(id=20, project_id=7, name="Em Progresso", position=1)
    repo.get_stages.return_value = {10: source, 20: dest}
    repo.get_project_owner_id.return_value = owner_id
    repo.move_to_stage.return_value = task

    await service.move_task(task, 20, author_id)

    repo.move_to_stage.assert_awaited_once_with(
        task, source, dest, author_id, {owner_id, responsible_id}
    )


async def test_move_task_excludes_the_mover_from_recipients(
    service: TaskService, repo: AsyncMock
) -> None:
    # quem move é, ao mesmo tempo, dono e responsável: ninguém é notificado.
    author_id = uuid4()
    task = Task(id=1, project_id=7, stage_id=10, title="T", position=0, responsible_id=author_id)
    source = Stage(id=10, project_id=7, name="Pendente", position=0)
    dest = Stage(id=20, project_id=7, name="Em Progresso", position=1)
    repo.get_stages.return_value = {10: source, 20: dest}
    repo.get_project_owner_id.return_value = author_id
    repo.move_to_stage.return_value = task

    await service.move_task(task, 20, author_id)

    repo.move_to_stage.assert_awaited_once_with(task, source, dest, author_id, set())


async def test_move_task_dedups_owner_and_responsible(
    service: TaskService, repo: AsyncMock
) -> None:
    author_id, owner_id = uuid4(), uuid4()
    task = Task(id=1, project_id=7, stage_id=10, title="T", position=0, responsible_id=owner_id)
    source = Stage(id=10, project_id=7, name="Pendente", position=0)
    dest = Stage(id=20, project_id=7, name="Em Progresso", position=1)
    repo.get_stages.return_value = {10: source, 20: dest}
    repo.get_project_owner_id.return_value = owner_id
    repo.move_to_stage.return_value = task

    await service.move_task(task, 20, author_id)

    repo.move_to_stage.assert_awaited_once_with(task, source, dest, author_id, {owner_id})


async def test_move_task_rejects_stage_of_other_project(
    service: TaskService, repo: AsyncMock
) -> None:
    task = Task(id=1, project_id=7, stage_id=10, title="T", position=0)
    repo.get_stages.return_value = {
        10: Stage(id=10, project_id=7, name="Pendente", position=0),
        20: Stage(id=20, project_id=99, name="Outra", position=0),
    }

    with pytest.raises(StageNotInProjectError):
        await service.move_task(task, 20, uuid4())

    repo.move_to_stage.assert_not_awaited()


async def test_move_task_rejects_unknown_stage(service: TaskService, repo: AsyncMock) -> None:
    task = Task(id=1, project_id=7, stage_id=10, title="T", position=0)
    repo.get_stages.return_value = {10: Stage(id=10, project_id=7, name="Pendente", position=0)}

    with pytest.raises(StageNotInProjectError):
        await service.move_task(task, 20, uuid4())

    repo.move_to_stage.assert_not_awaited()


async def test_move_task_to_same_column_is_noop(service: TaskService, repo: AsyncMock) -> None:
    task = Task(id=1, project_id=7, stage_id=10, title="T", position=0)
    repo.get_stages.return_value = {10: Stage(id=10, project_id=7, name="Pendente", position=0)}

    result = await service.move_task(task, 10, uuid4())

    assert result is task
    repo.move_to_stage.assert_not_awaited()


async def test_update_task_applies_changes(service: TaskService, repo: AsyncMock) -> None:
    task = Task(id=1, project_id=7, stage_id=10, title="Old", position=0)
    repo.update.return_value = task
    dto = UpdateTaskDTO(title="New", description="d", due_date=date(2026, 12, 31))

    await service.update_task(task, dto)

    repo.update.assert_awaited_once_with(
        task, {"title": "New", "description": "d", "due_date": date(2026, 12, 31)}
    )


async def test_update_task_ignores_explicit_null_title(
    service: TaskService, repo: AsyncMock
) -> None:
    task = Task(id=1, project_id=7, stage_id=10, title="Old", position=0)
    repo.update.return_value = task
    dto = UpdateTaskDTO.model_validate({"title": None, "due_date": None})

    await service.update_task(task, dto)

    repo.update.assert_awaited_once_with(task, {"due_date": None})


async def test_update_task_with_empty_body_is_noop(service: TaskService, repo: AsyncMock) -> None:
    task = Task(id=1, project_id=7, stage_id=10, title="Old", position=0)
    repo.update.return_value = task

    await service.update_task(task, UpdateTaskDTO())

    repo.update.assert_awaited_once_with(task, {})


async def test_list_history_delegates_to_repository(service: TaskService, repo: AsyncMock) -> None:
    task = Task(id=5, project_id=7, stage_id=10, title="T", position=0)
    history = [TaskHistory(id=1, task_id=5, from_stage_name="A", to_stage_name="B")]
    repo.list_history.return_value = history

    assert await service.list_history(task) == history
    repo.list_history.assert_awaited_once_with(5)
