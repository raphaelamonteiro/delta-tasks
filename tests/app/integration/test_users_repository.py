from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GlobalRole, Project, User
from app.domains.users.exceptions import (
    EmailAlreadyTakenError,
    UserHasDependenciesError,
    UserNotFoundError,
)
from app.domains.users.repository import UserRepository


@pytest.fixture
def repo(db_session: AsyncSession) -> UserRepository:
    return UserRepository(db_session)


async def add_user(
    db_session: AsyncSession, *, name: str = "U", email: str = "u@example.com"
) -> User:
    user = User(name=name, email=email, password_hash="x", global_role=GlobalRole.USER)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def test_get_by_id_returns_user(repo: UserRepository, db_session: AsyncSession) -> None:
    created = await add_user(db_session)

    assert (await repo.get_by_id(created.id)).id == created.id


async def test_get_by_id_missing_raises(repo: UserRepository) -> None:
    with pytest.raises(UserNotFoundError):
        await repo.get_by_id(uuid4())


async def test_list_paginates_and_counts(repo: UserRepository, db_session: AsyncSession) -> None:
    first = await add_user(db_session, email="a@example.com")
    second = await add_user(db_session, email="b@example.com")
    third = await add_user(db_session, email="c@example.com")

    page, total = await repo.list(limit=2, offset=0)
    assert total == 3
    assert [u.id for u in page] == [first.id, second.id]

    tail, total = await repo.list(limit=2, offset=2)
    assert total == 3
    assert [u.id for u in tail] == [third.id]


async def test_update_changes_fields(repo: UserRepository, db_session: AsyncSession) -> None:
    created = await add_user(db_session)

    updated = await repo.update(created.id, {"name": "Renamed", "global_role": GlobalRole.ADMIN})

    assert updated.name == "Renamed"
    assert updated.global_role == GlobalRole.ADMIN


async def test_update_duplicate_email_raises(
    repo: UserRepository, db_session: AsyncSession
) -> None:
    await add_user(db_session, email="taken@example.com")
    target = await add_user(db_session, email="target@example.com")

    with pytest.raises(EmailAlreadyTakenError):
        await repo.update(target.id, {"email": "taken@example.com"})


async def test_update_missing_user_raises(repo: UserRepository) -> None:
    with pytest.raises(UserNotFoundError):
        await repo.update(uuid4(), {"name": "X"})


async def test_delete_removes_user(repo: UserRepository, db_session: AsyncSession) -> None:
    created = await add_user(db_session)

    await repo.delete(created.id)

    with pytest.raises(UserNotFoundError):
        await repo.get_by_id(created.id)


async def test_delete_missing_user_raises(repo: UserRepository) -> None:
    with pytest.raises(UserNotFoundError):
        await repo.delete(uuid4())


async def test_delete_user_with_dependencies_raises(
    repo: UserRepository, db_session: AsyncSession
) -> None:
    owner = await add_user(db_session, email="owner@example.com")
    db_session.add(Project(name="Project", owner_id=owner.id))
    await db_session.commit()

    with pytest.raises(UserHasDependenciesError):
        await repo.delete(owner.id)
