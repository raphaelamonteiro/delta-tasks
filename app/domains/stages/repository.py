from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Stage


class StageRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, project_id: int, name: str) -> Stage:
        next_position = (
            select(func.coalesce(func.max(Stage.position), -1) + 1)
            .where(Stage.project_id == project_id)
            .scalar_subquery()
        )
        stage = Stage(project_id=project_id, name=name, position=next_position)
        self.db.add(stage)
        await self.db.commit()
        await self.db.refresh(stage)
        return stage

    async def get(self, stage_id: int) -> Stage | None:
        result = await self.db.execute(
            select(Stage).where(Stage.id == stage_id).options(selectinload(Stage.tasks))
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: int) -> Sequence[Stage]:
        result = await self.db.execute(
            select(Stage).where(Stage.project_id == project_id).order_by(Stage.position)
        )
        return result.scalars().all()

    async def update(self, stage: Stage, name: str) -> Stage:
        stage.name = name
        await self.db.commit()
        return stage

    async def reorder(self, stages: Sequence[Stage], ordered_ids: Sequence[int]) -> list[Stage]:
        by_id = {stage.id: stage for stage in stages}
        reordered = [by_id[stage_id] for stage_id in ordered_ids]
        for position, stage in enumerate(reordered):
            stage.position = position
        await self.db.commit()
        return reordered

    async def delete(self, stage: Stage) -> None:
        await self.db.delete(stage)
        await self.db.commit()
