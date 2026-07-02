from app.db.models import Stage
from app.domains.stages.exceptions import StageNotFoundError
from app.domains.stages.schemas import (CreateStageDTO, UpdateStageDTO)

class StageService:
    def __init__(self, repo):
        self.repo = repo

    async def create_stage( self, dto: CreateStageDTO):
        return await self.repo.create(project_id=dto.project_id, name=dto.name, position=0,)


    async def get_stage(self, stage_id: int ) -> Stage:
        stage = await self.repo.get(stage_id)
        if stage is None:
            raise StageNotFoundError(stage_id)
        return stage

    async def list_stages(self, project_id: int):
        return await self.repo.list_by_project(project_id)

    async def update_stage(self, stage: Stage, dto: UpdateStageDTO):
        return await self.repo.update(stage, dto.name)


    async def delete_stage(self, stage):

        if stage.tasks:
            raise ValueError("Cannot delete stage with tasks. Move tasks first.")
        await self.repo.delete(stage)