from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.logger import get_logger
from app.domains.auth.dependencies import get_current_user, require_admin
from app.domains.users.dependencies import UserServiceDep
from app.domains.users.exceptions import (
    EmailAlreadyTakenError,
    UserHasDependenciesError,
    UserNotFoundError,
)
from app.domains.users.schemas import UpdateUserDTO, UserListResponse, UserResponse
from app.domains.users.swagger_utils import (
    delete_user_swagger,
    get_user_swagger,
    list_users_swagger,
    update_user_swagger,
)

logger = get_logger("app.users.router")

users_router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(get_current_user)],
)


@users_router.get("", **list_users_swagger)
async def list_users(
    service: UserServiceDep,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> UserListResponse:
    users, total = await service.list_users(limit=limit, offset=offset)
    return UserListResponse(
        items=[UserResponse.model_validate(user) for user in users],
        total=total,
        limit=limit,
        offset=offset,
    )


@users_router.get("/{user_id}", **get_user_swagger)
async def get_user(user_id: UUID, service: UserServiceDep) -> UserResponse:
    try:
        user = await service.get_user(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        ) from exc

    return UserResponse.model_validate(user)


@users_router.patch(
    "/{user_id}",
    dependencies=[Depends(require_admin)],
    **update_user_swagger,
)
async def update_user(
    user_id: UUID,
    dto: UpdateUserDTO,
    service: UserServiceDep,
) -> UserResponse:
    try:
        user = await service.update_user(user_id, dto)
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        ) from exc
    except EmailAlreadyTakenError as exc:
        logger.warning("Update attempt with existing email")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        ) from exc

    return UserResponse.model_validate(user)


@users_router.delete(
    "/{user_id}",
    dependencies=[Depends(require_admin)],
    **delete_user_swagger,
)
async def delete_user(user_id: UUID, service: UserServiceDep) -> None:
    try:
        await service.delete_user(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        ) from exc
    except UserHasDependenciesError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User has related records and cannot be deleted.",
        ) from exc
