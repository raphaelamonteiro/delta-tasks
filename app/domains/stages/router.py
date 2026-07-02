from fastapi import APIRouter, Depends, HTTPException, status

from app.domains.auth.dependencies import CurrentUserDep, get_current_user
from app.domains.stages.dependencies import StageServiceDep
from app.domains.stages.exceptions import StageNotFoundError
from app.domains.stages.schemas import (CreateStageDTO, UpdateStageDTO, StageResponse)

stages_router = APIRouter(prefix="/stages",
    tags=["Stages"], dependencies=[Depends(get_current_user)])

@stages_router.post("", response_model=StageResponse, status_code=status.HTTP_201_CREATED)
async def create_stage( dto: CreateStageDTO, service: StageServiceDep):
    stage = await service.create_stage(dto)
    return StageResponse.model_validate(stage)


@stages_router.get("/{stage_id}", response_model=StageResponse,)
async def get_stage( stage_id: int, service: StageServiceDep):
    try:
        stage = await service.get_stage(stage_id)
    except StageNotFoundError:
        raise HTTPException(status_code=404, detail="Stage not found.")
    return StageResponse.model_validate(stage)


@stages_router.get( "/project/{project_id}", response_model=list[StageResponse])
async def list_project_stages( project_id: int,
    service: StageServiceDep): 
    stages = await service.list_stages(project_id)

    return [StageResponse.model_validate(stage) for stage in stages]

@stages_router.patch("/{stage_id}", response_model=StageResponse)
async def update_stage(stage_id: int, dto: UpdateStageDTO, service: StageServiceDep):
    try:
        stage = await service.get_stage(stage_id)
    except StageNotFoundError:
        raise HTTPException(status_code=404, detail="Stage not found.")
    stage = await service.update_stage(stage, dto)
    return StageResponse.model_validate(stage)


@stages_router.delete("/{stage_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_stage(stage_id: int, service: StageServiceDep):
    try:
        stage = await service.get_stage(stage_id)
    except StageNotFoundError:
        raise HTTPException(status_code=404, detail="Stage not found.")

    try:
        await service.delete_stage(stage)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return None