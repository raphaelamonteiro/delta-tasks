from uuid import uuid4

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GlobalRole, Project, ProjectMember, ProjectRole, User
from app.domains.auth.exceptions import EmailAlreadyExistsError
from app.domains.auth.principal import CurrentUser
from app.domains.auth.repository import AuthRepository
from app.domains.auth.schemas import CreateUserDTO


@pytest.fixture
def repo(db_session: AsyncSession) -> AuthRepository:
    return AuthRepository(db_session)


def make_dto(email: str = "new@example.com") -> CreateUserDTO:
    return CreateUserDTO(name="New", email=email, password_hash="hashed")


async def test_create_persists_user_with_defaults(repo: AuthRepository) -> None:
    user = await repo.create(make_dto())

    assert user.id is not None
    assert user.global_role == GlobalRole.USER
    assert user.is_active is True


async def test_create_duplicate_email_raises(repo: AuthRepository) -> None:
    await repo.create(make_dto())

    with pytest.raises(EmailAlreadyExistsError):
        await repo.create(make_dto())


async def test_get_by_email_returns_match_or_none(repo: AuthRepository) -> None:
    created = await repo.create(make_dto())

    found = await repo.get_by_email("new@example.com")
    assert found is not None
    assert found.id == created.id
    assert await repo.get_by_email("missing@example.com") is None


async def test_get_by_id_returns_match_or_none(repo: AuthRepository) -> None:
    created = await repo.create(make_dto())

    found = await repo.get_by_id(created.id)
    assert found is not None
    assert found.id == created.id
    assert await repo.get_by_id(uuid4()) is None


async def test_update_password_hash_persists(
    repo: AuthRepository, db_session: AsyncSession
) -> None:
    created = await repo.create(make_dto())

    await repo.update_password_hash(created, "new-hash")

    await db_session.refresh(created)
    assert created.password_hash == "new-hash"


async def test_create_inactive_user_is_not_returned_as_active(
    repo: AuthRepository, db_session: AsyncSession
) -> None:
    user = User(name="Off", email="off@example.com", password_hash="x", is_active=False)
    db_session.add(user)
    await db_session.commit()

    fetched = await repo.get_by_email("off@example.com")
    assert fetched is not None
    assert fetched.is_active is False


async def test_get_by_id_eager_loads_project_memberships(
    repo: AuthRepository, db_session: AsyncSession
) -> None:
    owner = await repo.create(make_dto(email="owner@example.com"))
    project = Project(name="Board", owner_id=owner.id)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    db_session.add(ProjectMember(project_id=project.id, user_id=owner.id, role=ProjectRole.OWNER))
    await db_session.commit()

    fetched = await repo.get_by_id(owner.id)
    assert fetched is not None

    assert "memberships" not in inspect(fetched).unloaded

    principal = CurrentUser.from_user(fetched)
    assert principal.role_in(project.id) is ProjectRole.OWNER
    assert principal.is_member(project.id) is True
