import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.region import Region


class RegionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, region: Region) -> Region:
        self._session.add(region)
        await self._session.flush()
        await self._session.refresh(region)
        return region

    async def get_by_id(self, region_id: uuid.UUID) -> Region | None:
        return await self._session.get(Region, region_id)

    async def get_by_name(self, name: str) -> Region | None:
        result = await self._session.execute(
            select(Region).where(Region.name == name)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Region]:
        result = await self._session.execute(
            select(Region).order_by(Region.name)
        )
        return list(result.scalars().all())
