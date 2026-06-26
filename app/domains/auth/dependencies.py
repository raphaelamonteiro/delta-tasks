from typing import Annotated

from fastapi import Depends

from app.core.security import PasswordSecurity
from app.db.dependencies import PgSessionDep
from app.domains.auth.repository import AuthRepository
from app.domains.auth.service import AuthService

password_security = PasswordSecurity()


def get_auth_repository(db: PgSessionDep) -> AuthRepository:
    return AuthRepository(db)


AuthRepositoryDep = Annotated[AuthRepository, Depends(get_auth_repository)]


def get_auth_service(auth_repo: AuthRepositoryDep) -> AuthService:
    return AuthService(repo=auth_repo, sec=password_security)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
