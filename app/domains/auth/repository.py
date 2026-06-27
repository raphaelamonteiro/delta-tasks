from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import User
from app.domains.auth.exceptions import EmailAlreadyExistsError
from app.domains.auth.schemas import CreateUserDTO


class AuthRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id).options(selectinload(User.memberships))
        )
        return result.scalars().first()

    async def update_password_hash(self, user: User, password_hash: str) -> None:
        user.password_hash = password_hash
        await self.db.commit()

    async def create(self, dto: CreateUserDTO) -> User:
        user = User(
            name=dto.name,
            email=dto.email,
            password_hash=dto.password_hash,
        )
        self.db.add(user)
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise EmailAlreadyExistsError(dto.email) from exc

        await self.db.refresh(user)
        return user
