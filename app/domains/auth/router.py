from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.core.logger import get_logger
from app.domains.auth.cookies import (
    REFRESH_COOKIE_NAME,
    clear_auth_cookies,
    set_access_cookie,
    set_auth_cookies,
)
from app.domains.auth.dependencies import (
    AuthServiceDep,
    CurrentUserDep,
    require_admin,
)
from app.domains.auth.exceptions import (
    EmailAlreadyExistsError,
    InactiveUserError,
    InvalidCredentialsError,
    SamePasswordError,
)
from app.domains.auth.schemas import (
    AuthenticatedUser,
    ChangePasswordDTO,
    LoginDTO,
    RegisterUserDTO,
    RegisterUserResponse,
)
from app.domains.auth.swagger_utils import (
    change_password_swagger,
    login_swagger,
    logout_swagger,
    me_swagger,
    refresh_swagger,
    register_user_swagger,
)

logger = get_logger("app.auth.router")

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post("/register", dependencies=[Depends(require_admin)], **register_user_swagger)
async def register_user(
    dto: RegisterUserDTO,
    service: AuthServiceDep,
) -> RegisterUserResponse:
    try:
        user = await service.register_user(dto)
    except EmailAlreadyExistsError as exc:
        logger.warning("Registration attempt with existing email")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        ) from exc

    return RegisterUserResponse.model_validate(user)


@auth_router.post("/login", **login_swagger)
async def login(
    dto: LoginDTO,
    response: Response,
    service: AuthServiceDep,
) -> AuthenticatedUser:
    try:
        result = await service.login(dto)
    except (InvalidCredentialsError, InactiveUserError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        ) from exc

    set_auth_cookies(response, result.access_token, result.refresh_token)
    return AuthenticatedUser.model_validate(result.user)


@auth_router.post("/refresh", **refresh_swagger)
async def refresh(
    request: Request,
    response: Response,
    service: AuthServiceDep,
) -> AuthenticatedUser:
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token.",
        )

    try:
        result = await service.refresh_session(token)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        ) from exc

    set_access_cookie(response, result.access_token)
    return AuthenticatedUser.model_validate(result.user)


@auth_router.post("/logout", **logout_swagger)
async def logout(response: Response, _user: CurrentUserDep) -> None:
    clear_auth_cookies(response)


@auth_router.get("/me", **me_swagger)
async def me(user: CurrentUserDep) -> AuthenticatedUser:
    return AuthenticatedUser.model_validate(user)


@auth_router.patch("/me/password", **change_password_swagger)
async def change_password(
    dto: ChangePasswordDTO,
    user: CurrentUserDep,
    service: AuthServiceDep,
) -> None:
    try:
        await service.change_password(user.user, dto)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect.",
        ) from exc
    except SamePasswordError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current one.",
        ) from exc
