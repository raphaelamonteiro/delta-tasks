from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.jwt import JWTService
from app.core.security import PasswordSecurity
from app.db.models import GlobalRole, User
from app.domains.auth.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    SamePasswordError,
)
from app.domains.auth.schemas import ChangePasswordDTO, CreateUserDTO, LoginDTO, RegisterUserDTO
from app.domains.auth.service import AuthService

PASSWORD = "Sup3rSecret!"

security = PasswordSecurity()
jwt_service = JWTService()


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(repo: AsyncMock) -> AuthService:
    return AuthService(repo=repo, sec=security, jwt=jwt_service)


def build_user(*, password: str = PASSWORD, is_active: bool = True) -> User:
    return User(
        id=uuid4(),
        name="User",
        email="user@example.com",
        password_hash=security.generate_password_hash(password),
        global_role=GlobalRole.USER,
        is_active=is_active,
    )


async def test_register_user_hashes_password_and_persists(
    service: AuthService, repo: AsyncMock
) -> None:
    created = build_user()
    repo.create.return_value = created

    result = await service.register_user(
        RegisterUserDTO(name="User", email="user@example.com", password=PASSWORD)
    )

    assert result is created
    dto = repo.create.await_args.args[0]
    assert isinstance(dto, CreateUserDTO)
    assert dto.password_hash != PASSWORD
    assert security.verify_password(PASSWORD, dto.password_hash)


async def test_authenticate_success_returns_user(service: AuthService, repo: AsyncMock) -> None:
    user = build_user()
    repo.get_by_email.return_value = user

    result = await service.authenticate(LoginDTO(email=user.email, password=PASSWORD))

    assert result is user
    repo.update_password_hash.assert_not_awaited()


async def test_authenticate_unknown_email_raises_invalid_credentials(
    service: AuthService, repo: AsyncMock
) -> None:
    repo.get_by_email.return_value = None

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate(LoginDTO(email="ghost@example.com", password=PASSWORD))


async def test_authenticate_wrong_password_raises_invalid_credentials(
    service: AuthService, repo: AsyncMock
) -> None:
    repo.get_by_email.return_value = build_user()

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate(LoginDTO(email="user@example.com", password="wrong-password"))


async def test_authenticate_inactive_user_raises_inactive_error(
    service: AuthService, repo: AsyncMock
) -> None:
    repo.get_by_email.return_value = build_user(is_active=False)

    with pytest.raises(InactiveUserError):
        await service.authenticate(LoginDTO(email="user@example.com", password=PASSWORD))


async def test_authenticate_rehashes_when_needed(
    service: AuthService, repo: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = build_user()
    repo.get_by_email.return_value = user
    monkeypatch.setattr(service.sec, "needs_rehash", lambda _hash: True)

    await service.authenticate(LoginDTO(email=user.email, password=PASSWORD))

    repo.update_password_hash.assert_awaited_once()


async def test_login_issues_access_and_refresh_tokens(
    service: AuthService, repo: AsyncMock
) -> None:
    user = build_user()
    repo.get_by_email.return_value = user

    result = await service.login(LoginDTO(email=user.email, password=PASSWORD))

    access = jwt_service.decode_access_token(result.access_token)
    refresh = jwt_service.decode_refresh_token(result.refresh_token)
    assert access["sub"] == str(user.id)
    assert access["role"] == GlobalRole.USER.value
    assert refresh["sub"] == str(user.id)


async def test_refresh_session_returns_new_access_token(
    service: AuthService, repo: AsyncMock
) -> None:
    user = build_user()
    repo.get_by_id.return_value = user
    refresh_token = jwt_service.create_refresh_token(str(user.id))

    result = await service.refresh_session(refresh_token)

    assert jwt_service.decode_access_token(result.access_token)["sub"] == str(user.id)


async def test_refresh_session_rejects_access_token(service: AuthService) -> None:
    access_token = jwt_service.create_access_token(str(uuid4()))

    with pytest.raises(InvalidCredentialsError):
        await service.refresh_session(access_token)


async def test_refresh_session_rejects_inactive_user(service: AuthService, repo: AsyncMock) -> None:
    repo.get_by_id.return_value = build_user(is_active=False)
    refresh_token = jwt_service.create_refresh_token(str(uuid4()))

    with pytest.raises(InvalidCredentialsError):
        await service.refresh_session(refresh_token)


async def test_get_user_from_access_token_returns_user(
    service: AuthService, repo: AsyncMock
) -> None:
    user = build_user()
    repo.get_by_id.return_value = user
    access_token = jwt_service.create_access_token(str(user.id))

    assert await service.get_user_from_access_token(access_token) is user


async def test_get_user_from_access_token_rejects_garbage(service: AuthService) -> None:
    with pytest.raises(InvalidCredentialsError):
        await service.get_user_from_access_token("not-a-token")


async def test_change_password_wrong_current_raises_invalid_credentials(
    service: AuthService, repo: AsyncMock
) -> None:
    user = build_user()
    dto = ChangePasswordDTO(current_password="wrong-password", new_password="An0therPass!")

    with pytest.raises(InvalidCredentialsError):
        await service.change_password(user, dto)
    repo.update_password_hash.assert_not_awaited()


async def test_change_password_same_password_raises_same_password(
    service: AuthService, repo: AsyncMock
) -> None:
    user = build_user()
    dto = ChangePasswordDTO(current_password=PASSWORD, new_password=PASSWORD)

    with pytest.raises(SamePasswordError):
        await service.change_password(user, dto)
    repo.update_password_hash.assert_not_awaited()


async def test_change_password_success_persists_new_hash(
    service: AuthService, repo: AsyncMock
) -> None:
    user = build_user()
    dto = ChangePasswordDTO(current_password=PASSWORD, new_password="An0therPass!")

    await service.change_password(user, dto)

    repo.update_password_hash.assert_awaited_once()
    new_hash = repo.update_password_hash.await_args.args[1]
    assert security.verify_password("An0therPass!", new_hash)
