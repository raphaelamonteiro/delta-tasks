from collections.abc import Sequence
from uuid import UUID

from app.core.logger import get_logger
from app.core.security import PasswordSecurity
from app.db.models import User
from app.domains.users.repository import UserRepository
from app.domains.users.schemas import UpdateUserDTO

logger = get_logger("app.users.service")


class UserService:
    def __init__(self, repo: UserRepository, sec: PasswordSecurity):
        self.repo = repo
        self.sec = sec

    async def get_user(self, user_id: UUID) -> User:
        return await self.repo.get_by_id(user_id)

    async def list_users(self, limit: int, offset: int) -> tuple[Sequence[User], int]:
        return await self.repo.list(limit=limit, offset=offset)

    async def update_user(self, user_id: UUID, dto: UpdateUserDTO) -> User:
        changes = dto.model_dump(exclude_unset=True)
        password = changes.pop("password", None)
        if password is not None:
            changes["password_hash"] = self.sec.generate_password_hash(password)

        user = await self.repo.update(user_id, changes)
        logger.info("User updated", extra={"user_id": str(user.id)})
        return user

    async def delete_user(self, user_id: UUID) -> None:
        await self.repo.delete(user_id)
        logger.info("User deleted", extra={"user_id": str(user_id)})
