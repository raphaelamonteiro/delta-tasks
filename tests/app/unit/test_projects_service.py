from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.db.models import Project
from app.domains.projects.exceptions import ProjectNotFoundError
from app.domains.projects.schemas import CreateProjectDTO, UpdateProjectDTO
from app.domains.projects.service import DEFAULT_COLUMNS, ProjectService


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(repo: AsyncMock) -> ProjectService:
    return ProjectService(repo=repo)


async def test_create_project_delegates_with_default_columns(
    service: ProjectService, repo: AsyncMock
) -> None:
    created = Project(id=1, name="Quadro", owner_id=uuid4())
    repo.create.return_value = created
    owner_id = uuid4()
    dto = CreateProjectDTO(name="Quadro")

    result = await service.create_project(owner_id, dto)

    assert result is created
    repo.create.assert_awaited_once_with(owner_id, dto, DEFAULT_COLUMNS)


def test_default_columns_follow_rn005() -> None:
    assert DEFAULT_COLUMNS == ("Pendente", "Em Progresso", "Em Revisão", "Concluído")


async def test_list_user_projects_delegates_to_repository(
    service: ProjectService, repo: AsyncMock
) -> None:
    projects = [Project(id=1, name="A", owner_id=uuid4())]
    repo.list_for_user.return_value = projects

    user_id = uuid4()
    assert await service.list_user_projects(user_id) == projects
    repo.list_for_user.assert_awaited_once_with(user_id)


async def test_get_board_returns_project(service: ProjectService, repo: AsyncMock) -> None:
    project = Project(id=1, name="A", owner_id=uuid4())
    repo.get_board.return_value = project

    assert await service.get_board(1) is project
    repo.get_board.assert_awaited_once_with(1)


async def test_get_board_raises_when_missing(service: ProjectService, repo: AsyncMock) -> None:
    repo.get_board.return_value = None

    with pytest.raises(ProjectNotFoundError):
        await service.get_board(999)


async def test_get_project_raises_when_missing(service: ProjectService, repo: AsyncMock) -> None:
    repo.get.return_value = None

    with pytest.raises(ProjectNotFoundError):
        await service.get_project(999)


async def test_update_project_applies_changes(service: ProjectService, repo: AsyncMock) -> None:
    project = Project(id=1, name="Old", owner_id=uuid4())
    repo.update.return_value = project
    dto = UpdateProjectDTO(name="New", description="d")

    await service.update_project(project, dto)

    repo.update.assert_awaited_once_with(project, {"name": "New", "description": "d"})


async def test_update_project_ignores_explicit_null_name(
    service: ProjectService, repo: AsyncMock
) -> None:
    project = Project(id=1, name="Old", owner_id=uuid4())
    repo.update.return_value = project
    dto = UpdateProjectDTO.model_validate({"name": None, "description": None})

    await service.update_project(project, dto)

    repo.update.assert_awaited_once_with(project, {"description": None})


async def test_update_project_with_empty_body_is_noop(
    service: ProjectService, repo: AsyncMock
) -> None:
    project = Project(id=1, name="Old", owner_id=uuid4())
    repo.update.return_value = project

    await service.update_project(project, UpdateProjectDTO())

    repo.update.assert_awaited_once_with(project, {})


async def test_delete_project_delegates(service: ProjectService, repo: AsyncMock) -> None:
    project = Project(id=1, name="X", owner_id=uuid4())

    await service.delete_project(project)

    repo.delete.assert_awaited_once_with(project)
