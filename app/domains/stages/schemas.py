from pydantic import Field

from app.core.schemas import BaseDTO


class CreateStageDTO(BaseDTO):
    name: str = Field(min_length=1, max_length=100)


class UpdateStageDTO(BaseDTO):
    name: str = Field(min_length=1, max_length=100)


class ReorderStagesDTO(BaseDTO):
    stage_ids: list[int]