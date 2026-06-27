from collections.abc import Callable
from typing import Any, NamedTuple
from uuid import UUID

from app.core.jwt import JWTService, TokenError
from app.core.logger import get_logger
from app.core.security import PasswordSecurity
from app.db.models import User
from app.domains.auth.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    SamePasswordError,
)
from app.domains.auth.repository import AuthRepository
from app.domains.auth.schemas import (
    ChangePasswordDTO,
    CreateUserDTO,
    LoginDTO,
    RegisterUserDTO,
)

logger = get_logger("app.auth.service")


class LoginResult(NamedTuple):
    user: User
    access_token: str
    refresh_token: str


class RefreshResult(NamedTuple):
    user: User
    access_token: str


class AuthService:
    def __init__(self, repo: AuthRepository, sec: PasswordSecurity, jwt: JWTService):
        self.repo = repo
        self.sec = sec
        self.jwt = jwt

    async def register_user(self, dto: RegisterUserDTO) -> User:
        password_hash = self.sec.generate_password_hash(dto.password)
        user = await self.repo.create(
            CreateUserDTO(name=dto.name, email=dto.email, password_hash=password_hash)
        )
        logger.info("User registered", extra={"user_id": str(user.id)})
        return user

    async def authenticate(self, dto: LoginDTO) -> User:
        user = await self.repo.get_by_email(dto.email)
        if user is None or not self.sec.verify_password(dto.password, user.password_hash):
            logger.warning("Failed login attempt")
            raise InvalidCredentialsError("Invalid email or password")

        if not user.is_active:
            logger.warning("Login attempt on inactive account", extra={"user_id": str(user.id)})
            raise InactiveUserError(user.id)

        if self.sec.needs_rehash(user.password_hash):
            await self.repo.update_password_hash(
                user, self.sec.generate_password_hash(dto.password)
            )

        logger.info("User authenticated", extra={"user_id": str(user.id)})
        return user

    async def login(self, dto: LoginDTO) -> LoginResult:
        user = await self.authenticate(dto)
        return LoginResult(
            user=user,
            access_token=self._issue_access_token(user),
            refresh_token=self.jwt.create_refresh_token(str(user.id)),
        )

    async def refresh_session(self, refresh_token: str) -> RefreshResult:
        user = await self._user_from_token(refresh_token, self.jwt.decode_refresh_token)
        logger.info("Access token refreshed", extra={"user_id": str(user.id)})
        return RefreshResult(user=user, access_token=self._issue_access_token(user))

    async def get_user_from_access_token(self, access_token: str) -> User:
        return await self._user_from_token(access_token, self.jwt.decode_access_token)

    async def change_password(self, user: User, dto: ChangePasswordDTO) -> None:
        if not self.sec.verify_password(dto.current_password, user.password_hash):
            logger.warning(
                "Password change with wrong current password", extra={"user_id": str(user.id)}
            )
            raise InvalidCredentialsError("Current password is incorrect")

        if self.sec.verify_password(dto.new_password, user.password_hash):
            raise SamePasswordError("New password must differ from the current one")

        await self.repo.update_password_hash(
            user, self.sec.generate_password_hash(dto.new_password)
        )
        logger.info("Password changed", extra={"user_id": str(user.id)})

    def _issue_access_token(self, user: User) -> str:
        return self.jwt.create_access_token(str(user.id), {"role": user.global_role.value})

    async def _user_from_token(self, token: str, decoder: Callable[[str], dict[str, Any]]) -> User:
        try:
            payload = decoder(token)
            user_id = UUID(str(payload["sub"]))
        except (TokenError, KeyError, ValueError) as exc:
            raise InvalidCredentialsError("Invalid or expired token") from exc

        user = await self.repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise InvalidCredentialsError("Invalid or expired token")
        return user
