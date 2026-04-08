"""Fakes for unit testing — mirror the real repository/client interfaces."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.domain.enums import WeatherCondition
from app.domain.schemas.weather import WeatherData
from app.infrastructure.weather_client.base import WeatherClient


# ---------------------------------------------------------------------------
# Weather Client fake
# ---------------------------------------------------------------------------


class FakeWeatherClient(WeatherClient):
    """Returns a pre-configured weather response, no HTTP calls."""

    def __init__(
        self,
        condition: WeatherCondition = WeatherCondition.CLEAR,
        description: str = "clear sky",
        temperature_c: float = 25.0,
        wind_speed_ms: float = 1.5,
        city_name: str = "FakeCity",
        lat: float = 0.0,
        lon: float = 0.0,
    ) -> None:
        self._data = WeatherData(
            condition=condition,
            description=description,
            temperature_c=temperature_c,
            wind_speed_ms=wind_speed_ms,
            city_name=city_name,
            lat=lat,
            lon=lon,
        )

    async def get_current_weather(
        self,
        *,
        city: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
    ) -> WeatherData:
        return self._data


# ---------------------------------------------------------------------------
# Lightweight stand-ins for ORM objects used in fakes
# ---------------------------------------------------------------------------


@dataclass
class FakeIncentiveConfigRow:
    condition: str
    base_fare: float
    incentive_pct: float
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class FakeSnapshotRow:
    id: uuid.UUID
    region_id: uuid.UUID
    condition: str
    description: str
    temperature_c: float
    wind_speed_ms: float
    queried_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class FakeEvaluationRow:
    id: uuid.UUID
    snapshot_id: uuid.UUID
    region_id: uuid.UUID
    investment_level: str
    base_fare: float
    incentive_pct: float
    incentive_amt: float
    total_investment: float
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class FakeRegionRow:
    id: uuid.UUID
    name: str
    lat: float
    lon: float
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Repository fakes
# ---------------------------------------------------------------------------


class FakeConfigRepository:
    """In-memory incentive config store."""

    def __init__(
        self,
        incentive_pct_by_condition: dict[WeatherCondition, float] | None = None,
        base_fare: float = 120.0,
    ) -> None:
        self._configs: dict[str, FakeIncentiveConfigRow] = {}
        if incentive_pct_by_condition:
            for cond, pct in incentive_pct_by_condition.items():
                self._configs[cond.value] = FakeIncentiveConfigRow(
                    condition=cond.value, base_fare=base_fare, incentive_pct=pct
                )

    async def get_by_condition(
        self, condition: WeatherCondition
    ) -> FakeIncentiveConfigRow | None:
        return self._configs.get(condition.value)

    async def get_all(self) -> list[FakeIncentiveConfigRow]:
        return list(self._configs.values())

    async def update_by_condition(
        self, condition: WeatherCondition, *, base_fare: float, incentive_pct: float
    ) -> FakeIncentiveConfigRow | None:
        row = self._configs.get(condition.value)
        if row is None:
            return None
        row.base_fare = base_fare
        row.incentive_pct = incentive_pct
        return row


class FakeWeatherRepository:
    """In-memory weather snapshot store."""

    def __init__(self) -> None:
        self._snapshots: list[FakeSnapshotRow] = []

    async def save_snapshot(self, snapshot: Any) -> Any:
        if getattr(snapshot, "id", None) is None:
            snapshot.id = uuid.uuid4()
        self._snapshots.append(snapshot)
        return snapshot

    async def get_latest_snapshot(self, region_id: uuid.UUID) -> FakeSnapshotRow | None:
        for snap in reversed(self._snapshots):
            if snap.region_id == region_id:
                return snap
        return None

    async def get_by_region(
        self,
        region_id: uuid.UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FakeSnapshotRow]:
        results = [s for s in self._snapshots if s.region_id == region_id]
        return results[offset : offset + limit]


class FakeInvestmentRepository:
    """In-memory evaluation store."""

    def __init__(self) -> None:
        self._evaluations: list[FakeEvaluationRow] = []

    async def save_evaluation(self, evaluation: Any) -> Any:
        if getattr(evaluation, "id", None) is None:
            evaluation.id = uuid.uuid4()
        self._evaluations.append(evaluation)
        return evaluation

    async def get_history(
        self,
        *,
        region_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FakeEvaluationRow]:
        results = self._evaluations
        if region_id is not None:
            results = [e for e in results if e.region_id == region_id]
        return results[offset : offset + limit]


class FakeRegionRepository:
    """In-memory region store."""

    def __init__(self, regions: list[FakeRegionRow] | None = None) -> None:
        self._regions: list[FakeRegionRow] = regions or []

    async def create(self, region: Any) -> Any:
        # Assign an id if the object doesn't have one (e.g. ORM Region)
        if getattr(region, "id", None) is None:
            region.id = uuid.uuid4()
        if getattr(region, "created_at", None) is None:
            region.created_at = datetime.now(timezone.utc)
        self._regions.append(region)
        return region

    async def get_by_id(self, region_id: uuid.UUID) -> FakeRegionRow | None:
        for r in self._regions:
            if r.id == region_id:
                return r
        return None

    async def get_by_name(self, name: str) -> FakeRegionRow | None:
        for r in self._regions:
            if r.name == name:
                return r
        return None

    async def get_all(self) -> list[FakeRegionRow]:
        return list(self._regions)
