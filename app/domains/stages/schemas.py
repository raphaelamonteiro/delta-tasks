from pydantic import ConfigDict, Field

from app.core.schemas import BaseDTO


class CreateStageDTO(BaseDTO):
    project_id: int
    name: str = Field(min_length=1, max_length=100)


class UpdateStageDTO(BaseDTO):
    name: str = Field(min_length=1, max_length=100)


class ReorderStagesDTO(BaseDTO):
    stage_ids: list[int]


class StageResponse(BaseDTO):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    position: int