from collections.abc import Sequence

from app.db.models import Stage
from app.domains.stages.exceptions import InvalidStageOrderError, StageNotFoundError
from app.domains.stages.repository import StageRepository
from app.domains.stages.schemas import CreateStageDTO, UpdateStageDTO


class StageService:
    def __init__(self, repo: StageRepository):
        self.repo = repo

    async def create_stage(self, dto: CreateStageDTO) -> Stage:
        return await self.repo.create(project_id=dto.project_id, name=dto.name)

    async def get_stage(self, stage_id: int) -> Stage:
        stage = await self.repo.get(stage_id)
        if stage is None:
            raise StageNotFoundError(stage_id)
        return stage

    async def list_stages(self, project_id: int) -> Sequence[Stage]:
        return await self.repo.list_by_project(project_id)

    async def update_stage(self, stage: Stage, dto: UpdateStageDTO) -> Stage:
        return await self.repo.update(stage, dto.name)

    async def reorder_stages(self, project_id: int, stage_ids: Sequence[int]) -> list[Stage]:
        stages = await self.repo.list_by_project(project_id)
        if len(stage_ids) != len(stages) or set(stage_ids) != {stage.id for stage in stages}:
            raise InvalidStageOrderError(project_id)
        return await self.repo.reorder(stages, stage_ids)

    async def delete_stage(self, stage: Stage) -> None:
        if stage.tasks:
            raise ValueError("Cannot delete stage with tasks. Move tasks first.")
        await self.repo.delete(stage)
