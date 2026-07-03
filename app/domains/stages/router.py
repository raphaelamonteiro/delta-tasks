from fastapi import APIRouter, Depends, HTTPException, status

from app.db.models import ProjectRole
from app.domains.auth.dependencies import CurrentUserDep, get_current_user
from app.domains.auth.principal import CurrentUser
from app.domains.stages.dependencies import StageServiceDep
from app.domains.stages.exceptions import InvalidStageOrderError, StageNotFoundError
from app.domains.stages.schemas import (
    CreateStageDTO,
    ReorderStagesDTO,
    StageResponse,
    UpdateStageDTO,
)

stages_router = APIRouter(
    prefix="/stages",
    tags=["Stages"],
    dependencies=[Depends(get_current_user)],
)


def _require_member(project_id: int, user: CurrentUser) -> None:
    if not (user.is_admin or user.is_member(project_id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project.",
        )


def _require_owner(project_id: int, user: CurrentUser) -> None:
    if user.role_in(project_id) != ProjectRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can manage the board columns.",
        )


@stages_router.post("", response_model=StageResponse, status_code=status.HTTP_201_CREATED)
async def create_stage(
    dto: CreateStageDTO,
    user: CurrentUserDep,
    service: StageServiceDep,
) -> StageResponse:
    _require_owner(dto.project_id, user)
    stage = await service.create_stage(dto)
    return StageResponse.model_validate(stage)


@stages_router.get("/{stage_id}", response_model=StageResponse)
async def get_stage(
    stage_id: int,
    user: CurrentUserDep,
    service: StageServiceDep,
) -> StageResponse:
    try:
        stage = await service.get_stage(stage_id)
    except StageNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Stage not found.") from exc

    _require_member(stage.project_id, user)
    return StageResponse.model_validate(stage)


@stages_router.get("/project/{project_id}", response_model=list[StageResponse])
async def list_project_stages(
    project_id: int,
    user: CurrentUserDep,
    service: StageServiceDep,
) -> list[StageResponse]:
    _require_member(project_id, user)
    stages = await service.list_stages(project_id)
    return [StageResponse.model_validate(stage) for stage in stages]


@stages_router.put("/project/{project_id}/reorder", response_model=list[StageResponse])
async def reorder_stages(
    project_id: int,
    dto: ReorderStagesDTO,
    user: CurrentUserDep,
    service: StageServiceDep,
) -> list[StageResponse]:
    _require_owner(project_id, user)
    try:
        stages = await service.reorder_stages(project_id, dto.stage_ids)
    except InvalidStageOrderError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="stage_ids must contain exactly the ids of the project's columns.",
        ) from exc
    return [StageResponse.model_validate(stage) for stage in stages]


@stages_router.patch("/{stage_id}", response_model=StageResponse)
async def update_stage(
    stage_id: int,
    dto: UpdateStageDTO,
    user: CurrentUserDep,
    service: StageServiceDep,
) -> StageResponse:
    try:
        stage = await service.get_stage(stage_id)
    except StageNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Stage not found.") from exc

    _require_owner(stage.project_id, user)
    stage = await service.update_stage(stage, dto)
    return StageResponse.model_validate(stage)


@stages_router.delete("/{stage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stage(
    stage_id: int,
    user: CurrentUserDep,
    service: StageServiceDep,
) -> None:
    try:
        stage = await service.get_stage(stage_id)
    except StageNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Stage not found.") from exc

    _require_owner(stage.project_id, user)

    try:
        await service.delete_stage(stage)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
