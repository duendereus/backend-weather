import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import InvestmentLevel, WeatherCondition
from app.domain.models.investment_evaluation import InvestmentEvaluation
from app.domain.models.region import Region
from app.domain.models.weather_snapshot import WeatherSnapshot
from app.repositories.investment_repository import InvestmentRepository
from app.repositories.region_repository import RegionRepository
from app.repositories.weather_repository import WeatherRepository


@pytest.mark.integration
class TestInvestmentRepository:
    async def _setup_snapshot(self, session: AsyncSession) -> tuple[Region, WeatherSnapshot]:
        region_repo = RegionRepository(session)
        weather_repo = WeatherRepository(session)

        region = await region_repo.create(Region(name="InvestCity", lat=4.0, lon=-74.0))
        snapshot = await weather_repo.save_snapshot(
            WeatherSnapshot(
                region_id=region.id,
                condition=WeatherCondition.THUNDERSTORM.value,
                description="thunderstorm",
                temperature_c=12.0,
                wind_speed_ms=8.0,
            )
        )
        return region, snapshot

    async def test_save_evaluation(self, db_session: AsyncSession) -> None:
        region, snapshot = await self._setup_snapshot(db_session)
        repo = InvestmentRepository(db_session)

        evaluation = InvestmentEvaluation(
            snapshot_id=snapshot.id,
            region_id=region.id,
            investment_level=InvestmentLevel.HIGH.value,
            base_fare=120.0,
            incentive_pct=60.0,
            incentive_amt=72.0,
            total_investment=192.0,
        )
        saved = await repo.save_evaluation(evaluation)
        assert saved.id is not None
        assert saved.investment_level == InvestmentLevel.HIGH.value

    async def test_get_history(self, db_session: AsyncSession) -> None:
        region, snapshot = await self._setup_snapshot(db_session)
        repo = InvestmentRepository(db_session)

        await repo.save_evaluation(
            InvestmentEvaluation(
                snapshot_id=snapshot.id,
                region_id=region.id,
                investment_level=InvestmentLevel.HIGH.value,
                base_fare=120.0,
                incentive_pct=60.0,
                incentive_amt=72.0,
                total_investment=192.0,
            )
        )

        history = await repo.get_history(region_id=region.id)
        assert len(history) >= 1
        assert history[0].region_id == region.id
