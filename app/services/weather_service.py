from __future__ import annotations

import logging
import uuid
from typing import Any, Protocol

from app.domain.schemas.weather import WeatherData
from app.infrastructure.weather_client.base import WeatherClient

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lightweight protocols so the service doesn't depend on concrete repos/models
# ---------------------------------------------------------------------------


class RegionRepoProto(Protocol):
    async def get_by_name(self, name: str) -> Any: ...
    async def create(self, region: Any) -> Any: ...


class WeatherRepoProto(Protocol):
    async def save_snapshot(self, snapshot: Any) -> Any: ...


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class WeatherService:
    def __init__(
        self,
        *,
        weather_client: WeatherClient,
        weather_repo: WeatherRepoProto,
        region_repo: RegionRepoProto,
    ) -> None:
        self._client = weather_client
        self._weather_repo = weather_repo
        self._region_repo = region_repo

    async def get_weather(
        self,
        *,
        city: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
    ) -> WeatherData:
        data = await self._client.get_current_weather(city=city, lat=lat, lon=lon)
        region = await self._get_or_create_region(data)
        await self._persist_snapshot(data, region_id=region.id)
        return data

    async def _get_or_create_region(self, data: WeatherData) -> Any:
        existing = await self._region_repo.get_by_name(data.city_name)
        if existing is not None:
            return existing

        from app.domain.models.region import Region

        region = Region(name=data.city_name, lat=data.lat, lon=data.lon)
        return await self._region_repo.create(region)

    async def _persist_snapshot(self, data: WeatherData, *, region_id: uuid.UUID) -> Any:
        from app.domain.models.weather_snapshot import WeatherSnapshot

        snapshot = WeatherSnapshot(
            region_id=region_id,
            condition=data.condition.value,
            description=data.description,
            temperature_c=data.temperature_c,
            wind_speed_ms=data.wind_speed_ms,
        )
        return await self._weather_repo.save_snapshot(snapshot)
