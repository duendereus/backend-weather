import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.weather_snapshot import WeatherSnapshot


class WeatherRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_snapshot(self, snapshot: WeatherSnapshot) -> WeatherSnapshot:
        self._session.add(snapshot)
        await self._session.flush()
        await self._session.refresh(snapshot)
        return snapshot

    async def get_latest_snapshot(self, region_id: uuid.UUID) -> WeatherSnapshot | None:
        result = await self._session.execute(
            select(WeatherSnapshot)
            .where(WeatherSnapshot.region_id == region_id)
            .order_by(WeatherSnapshot.queried_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_region(
        self,
        region_id: uuid.UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[WeatherSnapshot]:
        result = await self._session.execute(
            select(WeatherSnapshot)
            .where(WeatherSnapshot.region_id == region_id)
            .order_by(WeatherSnapshot.queried_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
