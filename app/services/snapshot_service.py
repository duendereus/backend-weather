from __future__ import annotations

import logging
import uuid
from typing import Any, Protocol

from app.domain.enums import WeatherCondition
from app.infrastructure.weather_client.base import WeatherClient
from app.services.investment_service import InvestmentService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Protocols
# ---------------------------------------------------------------------------


class RegionRepoProto(Protocol):
    async def get_all(self) -> list[Any]: ...


class WeatherRepoProto(Protocol):
    async def save_snapshot(self, snapshot: Any) -> Any: ...


class ConfigRepoProto(Protocol):
    async def get_by_condition(self, condition: WeatherCondition) -> Any: ...


class InvestmentRepoProto(Protocol):
    async def save_evaluation(self, evaluation: Any) -> Any: ...


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class SnapshotService:
    """Periodically queries weather for all registered regions and evaluates investment."""

    def __init__(
        self,
        *,
        weather_client: WeatherClient,
        weather_repo: WeatherRepoProto,
        region_repo: RegionRepoProto,
        config_repo: ConfigRepoProto,
        investment_repo: InvestmentRepoProto,
    ) -> None:
        self._client = weather_client
        self._weather_repo = weather_repo
        self._region_repo = region_repo
        self._investment_service = InvestmentService(
            config_repo=config_repo,
            investment_repo=investment_repo,
        )

    async def run(self) -> None:
        regions = await self._region_repo.get_all()
        logger.info("Snapshot job: processing %d regions", len(regions))

        for region in regions:
            try:
                await self._process_region(region)
            except Exception:
                logger.exception("Snapshot failed for region %s", region.name)

    async def _process_region(self, region: Any) -> None:
        data = await self._client.get_current_weather(lat=region.lat, lon=region.lon)

        from app.domain.models.weather_snapshot import WeatherSnapshot

        snapshot = WeatherSnapshot(
            region_id=region.id,
            condition=data.condition.value,
            description=data.description,
            temperature_c=data.temperature_c,
            wind_speed_ms=data.wind_speed_ms,
        )
        saved = await self._weather_repo.save_snapshot(snapshot)

        snapshot_id = saved.id
        await self._investment_service.calculate(
            condition=data.condition,
            region_id=region.id,
            snapshot_id=snapshot_id,
        )
