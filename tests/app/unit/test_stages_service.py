from unittest.mock import AsyncMock

import pytest

from app.db.models import Stage, Task
from app.domains.stages.exceptions import InvalidStageOrderError, StageNotFoundError
from app.domains.stages.schemas import CreateStageDTO, UpdateStageDTO
from app.domains.stages.service import StageService


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(repo: AsyncMock) -> StageService:
    return StageService(repo=repo)


async def test_create_stage_delegates_to_repository(
    service: StageService, repo: AsyncMock
) -> None:
    stage = Stage(id=5, project_id=7, name="Aprovação", position=4)
    repo.create.return_value = stage
    dto = CreateStageDTO(project_id=7, name="Aprovação")

    assert await service.create_stage(dto) is stage
    repo.create.assert_awaited_once_with(project_id=7, name="Aprovação")


async def test_get_stage_returns_stage(service: StageService, repo: AsyncMock) -> None:
    stage = Stage(id=1, project_id=7, name="Pendente", position=0)
    repo.get.return_value = stage

    assert await service.get_stage(1) is stage
    repo.get.assert_awaited_once_with(1)


async def test_get_stage_raises_when_missing(service: StageService, repo: AsyncMock) -> None:
    repo.get.return_value = None

    with pytest.raises(StageNotFoundError):
        await service.get_stage(999)


async def test_update_stage_delegates_with_new_name(
    service: StageService, repo: AsyncMock
) -> None:
    stage = Stage(id=1, project_id=7, name="Pendente", position=0)
    repo.update.return_value = stage

    await service.update_stage(stage, UpdateStageDTO(name="Backlog"))

    repo.update.assert_awaited_once_with(stage, "Backlog")


async def test_delete_empty_stage_delegates(service: StageService, repo: AsyncMock) -> None:
    stage = Stage(id=1, project_id=7, name="Pendente", position=0)

    await service.delete_stage(stage)

    repo.delete.assert_awaited_once_with(stage)


async def test_delete_stage_with_tasks_is_rejected(
    service: StageService, repo: AsyncMock
) -> None:
    stage = Stage(id=1, project_id=7, name="Pendente", position=0)
    stage.tasks = [Task(id=1, project_id=7, stage_id=1, title="T", position=0)]

    with pytest.raises(ValueError, match="Move tasks first"):
        await service.delete_stage(stage)

    repo.delete.assert_not_awaited()


async def test_reorder_stages_applies_new_order(service: StageService, repo: AsyncMock) -> None:
    first = Stage(id=1, project_id=7, name="A", position=0)
    second = Stage(id=2, project_id=7, name="B", position=1)
    repo.list_by_project.return_value = [first, second]
    repo.reorder.return_value = [second, first]

    result = await service.reorder_stages(7, [2, 1])

    assert result == [second, first]
    repo.reorder.assert_awaited_once_with([first, second], [2, 1])


async def test_reorder_stages_rejects_incomplete_ids(
    service: StageService, repo: AsyncMock
) -> None:
    repo.list_by_project.return_value = [
        Stage(id=1, project_id=7, name="A", position=0),
        Stage(id=2, project_id=7, name="B", position=1),
    ]

    with pytest.raises(InvalidStageOrderError):
        await service.reorder_stages(7, [1])

    repo.reorder.assert_not_awaited()


async def test_reorder_stages_rejects_unknown_ids(
    service: StageService, repo: AsyncMock
) -> None:
    repo.list_by_project.return_value = [
        Stage(id=1, project_id=7, name="A", position=0),
        Stage(id=2, project_id=7, name="B", position=1),
    ]

    with pytest.raises(InvalidStageOrderError):
        await service.reorder_stages(7, [1, 99])

    repo.reorder.assert_not_awaited()


async def test_reorder_stages_rejects_duplicated_ids(
    service: StageService, repo: AsyncMock
) -> None:
    repo.list_by_project.return_value = [
        Stage(id=1, project_id=7, name="A", position=0),
        Stage(id=2, project_id=7, name="B", position=1),
    ]

    with pytest.raises(InvalidStageOrderError):
        await service.reorder_stages(7, [1, 1])

    repo.reorder.assert_not_awaited()
