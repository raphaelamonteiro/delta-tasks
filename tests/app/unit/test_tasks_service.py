from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.db.models import Task
from app.domains.tasks.exceptions import ResponsibleNotMemberError, TaskNotFoundError
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
