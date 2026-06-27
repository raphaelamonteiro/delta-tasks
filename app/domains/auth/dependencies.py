from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.core.jwt import JWTService
from app.core.security import PasswordSecurity
from app.db.dependencies import PgSessionDep
from app.db.models import GlobalRole, User
from app.domains.auth.cookies import ACCESS_COOKIE_NAME
from app.domains.auth.exceptions import InvalidCredentialsError
from app.domains.auth.repository import AuthRepository
from app.domains.auth.service import AuthService

password_security = PasswordSecurity()
jwt_service = JWTService()


def get_auth_repository(db: PgSessionDep) -> AuthRepository:
    return AuthRepository(db)


AuthRepositoryDep = Annotated[AuthRepository, Depends(get_auth_repository)]


def get_auth_service(auth_repo: AuthRepositoryDep) -> AuthService:
    return AuthService(repo=auth_repo, sec=password_security, jwt=jwt_service)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def _not_authenticated() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated.",
    )


async def get_current_user(request: Request, service: AuthServiceDep) -> User:
    token = request.cookies.get(ACCESS_COOKIE_NAME)
    if not token:
        raise _not_authenticated()

    try:
        return await service.get_user_from_access_token(token)
    except InvalidCredentialsError as exc:
        raise _not_authenticated() from exc


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_admin(user: CurrentUserDep) -> User:
    if user.global_role != GlobalRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )
    return user


AdminUserDep = Annotated[User, Depends(require_admin)]
