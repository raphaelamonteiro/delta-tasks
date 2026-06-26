from fastapi import APIRouter, HTTPException, status

from app.core.logger import get_logger
from app.domains.auth.dependencies import AuthServiceDep
from app.domains.auth.exceptions import EmailAlreadyExistsError
from app.domains.auth.schemas import RegisterUserDTO, RegisterUserResponse
from app.domains.auth.swagger_utils import register_user_swagger

logger = get_logger("app.auth.user_router")

auth_router = APIRouter(prefix="/auth")


@auth_router.post("/register", tags=["Auth"], **register_user_swagger)
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
