from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.domains.users.exceptions import (
    EmailAlreadyTakenError,
    UserHasDependenciesError,
    UserNotFoundError,
)


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: UUID) -> User:
        user = await self.db.get(User, user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    async def list(self, limit: int, offset: int) -> tuple[Sequence[User], int]:
        total = await self.db.scalar(select(func.count()).select_from(User)) or 0
        result = await self.db.execute(
            select(User).order_by(User.created_at).limit(limit).offset(offset)
        )
        return result.scalars().all(), total

    async def update(self, user_id: UUID, changes: dict[str, Any]) -> User:
        user = await self.get_by_id(user_id)
        for field, value in changes.items():
            setattr(user, field, value)
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise EmailAlreadyTakenError(changes.get("email")) from exc

        await self.db.refresh(user)
        return user

    async def delete(self, user_id: UUID) -> None:
        user = await self.get_by_id(user_id)
        await self.db.delete(user)
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise UserHasDependenciesError(user_id) from exc
