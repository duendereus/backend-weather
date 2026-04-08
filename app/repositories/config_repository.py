from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import WeatherCondition
from app.domain.models.incentive_config import IncentiveConfig


class ConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[IncentiveConfig]:
        result = await self._session.execute(
            select(IncentiveConfig).order_by(IncentiveConfig.condition)
        )
        return list(result.scalars().all())

    async def get_by_condition(self, condition: WeatherCondition) -> IncentiveConfig | None:
        result = await self._session.execute(
            select(IncentiveConfig).where(IncentiveConfig.condition == condition.value)
        )
        return result.scalar_one_or_none()

    async def create(self, config: IncentiveConfig) -> IncentiveConfig:
        self._session.add(config)
        await self._session.flush()
        await self._session.refresh(config)
        return config

    async def update_by_condition(
        self,
        condition: WeatherCondition,
        *,
        base_fare: float,
        incentive_pct: float,
    ) -> IncentiveConfig | None:
        await self._session.execute(
            update(IncentiveConfig)
            .where(IncentiveConfig.condition == condition.value)
            .values(base_fare=base_fare, incentive_pct=incentive_pct)
        )
        await self._session.flush()
        return await self.get_by_condition(condition)
