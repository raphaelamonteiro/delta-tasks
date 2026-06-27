from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.security import PasswordSecurity
from app.db.models import GlobalRole, User
from app.domains.users.schemas import UpdateUserDTO
from app.domains.users.service import UserService

security = PasswordSecurity()


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(repo: AsyncMock) -> UserService:
    return UserService(repo=repo, sec=security)


def build_user() -> User:
    return User(id=uuid4(), name="U", email="u@example.com", password_hash="x")


async def test_get_user_delegates_to_repository(service: UserService, repo: AsyncMock) -> None:
    user = build_user()
    repo.get_by_id.return_value = user

    user_id = uuid4()
    assert await service.get_user(user_id) is user
    repo.get_by_id.assert_awaited_once_with(user_id)


async def test_list_users_delegates_to_repository(service: UserService, repo: AsyncMock) -> None:
    repo.list.return_value = ([], 0)

    assert await service.list_users(limit=10, offset=5) == ([], 0)
    repo.list.assert_awaited_once_with(limit=10, offset=5)


async def test_update_user_hashes_password_into_password_hash(
    service: UserService, repo: AsyncMock
) -> None:
    repo.update.return_value = build_user()

    user_id = uuid4()
    await service.update_user(user_id, UpdateUserDTO(password="N3wPassword!"))

    sent_id, changes = repo.update.await_args.args
    assert sent_id == user_id
    assert "password" not in changes
    assert security.verify_password("N3wPassword!", changes["password_hash"])


async def test_update_user_without_password_passes_changes_through(
    service: UserService, repo: AsyncMock
) -> None:
    repo.update.return_value = build_user()

    user_id = uuid4()
    await service.update_user(user_id, UpdateUserDTO(name="New Name", global_role=GlobalRole.ADMIN))

    _sent_id, changes = repo.update.await_args.args
    assert changes == {"name": "New Name", "global_role": GlobalRole.ADMIN}
    assert "password_hash" not in changes


async def test_delete_user_delegates_to_repository(service: UserService, repo: AsyncMock) -> None:
    user_id = uuid4()
    await service.delete_user(user_id)
    repo.delete.assert_awaited_once_with(user_id)
