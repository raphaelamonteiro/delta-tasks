from typing import Annotated

from fastapi import Depends

from app.core.security import PasswordSecurity
from app.db.dependencies import PgSessionDep
from app.domains.users.repository import UserRepository
from app.domains.users.service import UserService

password_security = PasswordSecurity()


def get_user_repository(db: PgSessionDep) -> UserRepository:
    return UserRepository(db)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_user_service(user_repo: UserRepositoryDep) -> UserService:
    return UserService(repo=user_repo, sec=password_security)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
