from sqlalchemy import delete, select
from typing import Any
from app.db.models import Stage
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class StageRepository:
     def __init__(self, db: AsyncSession) -> None:
        self.db = db

async def create(self, project_id: int, name: str, position: int):
    stage = Stage( project_id=project_id,
    name=name, position=position)

    self.db.add(stage)
    await self.db.commit()
    await self.db.refresh(stage)
    return stage

async def get(self, stage_id: int):
    result = await self.db.execute(select(Stage).where(Stage.id == stage_id))
    return result.scalar_one_or_none()


async def update(self, stage: Stage, name: str):
    stage.name = name
    await self.db.commit()
    return stage


async def delete(self, stage: Stage) -> None:
    await self.db.delete(stage)
    await self.db.commit()