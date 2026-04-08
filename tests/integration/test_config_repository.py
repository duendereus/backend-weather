import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import WeatherCondition
from app.domain.models.incentive_config import IncentiveConfig
from app.repositories.config_repository import ConfigRepository


@pytest.mark.integration
class TestConfigRepository:
    async def _seed_config(
        self, session: AsyncSession, condition: WeatherCondition, pct: float
    ) -> None:
        session.add(
            IncentiveConfig(condition=condition.value, base_fare=120.0, incentive_pct=pct)
        )
        await session.flush()

    async def test_get_by_condition(self, db_session: AsyncSession) -> None:
        await self._seed_config(db_session, WeatherCondition.RAIN, 35.0)
        repo = ConfigRepository(db_session)

        config = await repo.get_by_condition(WeatherCondition.RAIN)
        assert config is not None
        assert config.incentive_pct == 35.0

    async def test_get_by_condition_returns_none_when_missing(
        self, db_session: AsyncSession
    ) -> None:
        repo = ConfigRepository(db_session)
        result = await repo.get_by_condition(WeatherCondition.EXTREME)
        assert result is None

    async def test_get_all(self, db_session: AsyncSession) -> None:
        await self._seed_config(db_session, WeatherCondition.CLEAR, 0.0)
        await self._seed_config(db_session, WeatherCondition.SNOW, 60.0)
        repo = ConfigRepository(db_session)

        configs = await repo.get_all()
        assert len(configs) >= 2

    async def test_update_by_condition(self, db_session: AsyncSession) -> None:
        await self._seed_config(db_session, WeatherCondition.DRIZZLE, 15.0)
        repo = ConfigRepository(db_session)

        updated = await repo.update_by_condition(
            WeatherCondition.DRIZZLE, base_fare=150.0, incentive_pct=20.0
        )
        assert updated is not None
        assert updated.base_fare == 150.0
        assert updated.incentive_pct == 20.0
