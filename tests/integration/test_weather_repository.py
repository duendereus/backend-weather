import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import WeatherCondition
from app.domain.models.region import Region
from app.domain.models.weather_snapshot import WeatherSnapshot
from app.repositories.region_repository import RegionRepository
from app.repositories.weather_repository import WeatherRepository


@pytest.mark.integration
class TestWeatherRepository:
    async def _create_region(self, session: AsyncSession, name: str = "TestCity") -> Region:
        repo = RegionRepository(session)
        return await repo.create(Region(name=name, lat=19.43, lon=-99.13))

    async def test_save_and_get_latest_snapshot(self, db_session: AsyncSession) -> None:
        region = await self._create_region(db_session)
        repo = WeatherRepository(db_session)

        snapshot = WeatherSnapshot(
            region_id=region.id,
            condition=WeatherCondition.RAIN.value,
            description="light rain",
            temperature_c=17.0,
            wind_speed_ms=4.5,
        )
        saved = await repo.save_snapshot(snapshot)
        assert saved.id is not None

        latest = await repo.get_latest_snapshot(region.id)
        assert latest is not None
        assert latest.condition == WeatherCondition.RAIN.value

    async def test_get_by_region(self, db_session: AsyncSession) -> None:
        region = await self._create_region(db_session, name="HistoryCity")
        repo = WeatherRepository(db_session)

        for temp in [15.0, 20.0, 25.0]:
            await repo.save_snapshot(
                WeatherSnapshot(
                    region_id=region.id,
                    condition=WeatherCondition.CLOUDS.value,
                    description="overcast",
                    temperature_c=temp,
                    wind_speed_ms=2.0,
                )
            )

        results = await repo.get_by_region(region.id, limit=2)
        assert len(results) == 2
