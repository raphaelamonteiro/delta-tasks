import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GlobalRole, ProjectMember, ProjectRole, Stage, Task, User
from app.domains.projects.repository import ProjectRepository
from app.domains.projects.schemas import CreateProjectDTO

COLUMNS = ("Pendente", "Em Progresso", "Em Revisão", "Concluído")


@pytest.fixture
def repo(db_session: AsyncSession) -> ProjectRepository:
    return ProjectRepository(db_session)


async def make_owner(db_session: AsyncSession, email: str = "owner@example.com") -> User:
    user = User(name="Owner", email=email, password_hash="x", global_role=GlobalRole.USER)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def test_create_persists_project(repo: ProjectRepository, db_session: AsyncSession) -> None:
    owner = await make_owner(db_session)

    project = await repo.create(
        owner.id, CreateProjectDTO(name="Quadro", description="Time A"), COLUMNS
    )

    assert project.id is not None
    assert project.name == "Quadro"
    assert project.description == "Time A"
    assert project.owner_id == owner.id


async def test_create_registers_owner_as_member(
    repo: ProjectRepository, db_session: AsyncSession
) -> None:
    owner = await make_owner(db_session)

    project = await repo.create(owner.id, CreateProjectDTO(name="Quadro"), COLUMNS)

    result = await db_session.execute(
        select(ProjectMember).where(ProjectMember.project_id == project.id)
    )
    members = result.scalars().all()
    assert len(members) == 1
    assert members[0].user_id == owner.id
    assert members[0].role is ProjectRole.OWNER


async def test_create_generates_default_columns(
    repo: ProjectRepository, db_session: AsyncSession
) -> None:
    owner = await make_owner(db_session)

    project = await repo.create(owner.id, CreateProjectDTO(name="Quadro"), COLUMNS)

    assert [stage.name for stage in project.stages] == list(COLUMNS)

    result = await db_session.execute(
        select(Stage).where(Stage.project_id == project.id).order_by(Stage.position)
    )
    stages = result.scalars().all()
    assert [stage.name for stage in stages] == list(COLUMNS)
    assert [stage.position for stage in stages] == [0, 1, 2, 3]


async def test_create_without_description_stores_null(
    repo: ProjectRepository, db_session: AsyncSession
) -> None:
    owner = await make_owner(db_session)

    project = await repo.create(owner.id, CreateProjectDTO(name="Quadro"), COLUMNS)

    assert project.description is None


async def test_list_for_user_returns_only_member_projects(
    repo: ProjectRepository, db_session: AsyncSession
) -> None:
    alice = await make_owner(db_session, email="alice@example.com")
    bob = await make_owner(db_session, email="bob@example.com")
    alice_project = await repo.create(alice.id, CreateProjectDTO(name="Alice"), COLUMNS)
    await repo.create(bob.id, CreateProjectDTO(name="Bob"), COLUMNS)

    projects = await repo.list_for_user(alice.id)

    assert [project.id for project in projects] == [alice_project.id]


async def test_get_board_loads_columns_and_tasks(
    repo: ProjectRepository, db_session: AsyncSession
) -> None:
    owner = await make_owner(db_session)
    project = await repo.create(owner.id, CreateProjectDTO(name="Quadro"), COLUMNS)
    first_column = project.stages[0]
    db_session.add(
        Task(project_id=project.id, stage_id=first_column.id, title="Tarefa 1", position=0)
    )
    await db_session.commit()
    db_session.expunge_all()

    board = await repo.get_board(project.id)
    assert board is not None

    assert [column.name for column in board.stages] == list(COLUMNS)
    assert [task.title for task in board.stages[0].tasks] == ["Tarefa 1"]
    assert board.stages[1].tasks == []


async def test_get_board_returns_none_when_missing(repo: ProjectRepository) -> None:
    assert await repo.get_board(999999) is None


async def test_get_returns_project_or_none(
    repo: ProjectRepository, db_session: AsyncSession
) -> None:
    owner = await make_owner(db_session)
    project = await repo.create(owner.id, CreateProjectDTO(name="Quadro"), COLUMNS)

    fetched = await repo.get(project.id)
    assert fetched is not None
    assert fetched.id == project.id
    assert await repo.get(999999) is None


async def test_update_persists_changes(repo: ProjectRepository, db_session: AsyncSession) -> None:
    owner = await make_owner(db_session)
    project = await repo.create(
        owner.id, CreateProjectDTO(name="Antigo", description="d1"), COLUMNS
    )

    updated = await repo.update(project, {"name": "Novo", "description": "d2"})

    assert updated.name == "Novo"
    assert updated.description == "d2"
    db_session.expunge_all()
    reloaded = await repo.get(project.id)
    assert reloaded is not None
    assert reloaded.name == "Novo"


async def test_delete_removes_project_and_associations(
    repo: ProjectRepository, db_session: AsyncSession
) -> None:
    owner = await make_owner(db_session)
    project = await repo.create(owner.id, CreateProjectDTO(name="Quadro"), COLUMNS)
    project_id = project.id
    db_session.add(
        Task(project_id=project_id, stage_id=project.stages[0].id, title="T", position=0)
    )
    await db_session.commit()

    await repo.delete(project)

    assert await repo.get(project_id) is None
    members = await db_session.scalars(
        select(ProjectMember).where(ProjectMember.project_id == project_id)
    )
    stages = await db_session.scalars(select(Stage).where(Stage.project_id == project_id))
    tasks = await db_session.scalars(select(Task).where(Task.project_id == project_id))
    assert members.all() == []
    assert stages.all() == []
    assert tasks.all() == []
