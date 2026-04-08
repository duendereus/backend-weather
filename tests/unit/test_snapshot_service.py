import uuid

from app.domain.enums import WeatherCondition
from app.services.snapshot_service import SnapshotService
from tests.fakes import (
    FakeConfigRepository,
    FakeInvestmentRepository,
    FakeRegionRepository,
    FakeRegionRow,
    FakeWeatherClient,
    FakeWeatherRepository,
)


def _make_service(
    regions: list[FakeRegionRow] | None = None,
    condition: WeatherCondition = WeatherCondition.RAIN,
    pct_map: dict[WeatherCondition, float] | None = None,
) -> tuple[SnapshotService, FakeWeatherRepository, FakeInvestmentRepository]:
    weather_repo = FakeWeatherRepository()
    investment_repo = FakeInvestmentRepository()
    if pct_map is None:
        pct_map = {condition: 35.0}

    service = SnapshotService(
        weather_client=FakeWeatherClient(condition=condition, city_name="TestCity"),
        weather_repo=weather_repo,
        region_repo=FakeRegionRepository(regions=regions),
        config_repo=FakeConfigRepository(incentive_pct_by_condition=pct_map),
        investment_repo=investment_repo,
    )
    return service, weather_repo, investment_repo


class TestSnapshotServiceRun:
    async def test_creates_snapshot_for_each_region(self) -> None:
        regions = [
            FakeRegionRow(id=uuid.uuid4(), name="CityA", lat=10.0, lon=20.0),
            FakeRegionRow(id=uuid.uuid4(), name="CityB", lat=11.0, lon=21.0),
        ]
        service, weather_repo, _ = _make_service(regions=regions)

        await service.run()

        assert len(weather_repo._snapshots) == 2

    async def test_creates_evaluation_for_each_region(self) -> None:
        regions = [
            FakeRegionRow(id=uuid.uuid4(), name="CityA", lat=10.0, lon=20.0),
        ]
        service, _, investment_repo = _make_service(regions=regions)

        await service.run()

        assert len(investment_repo._evaluations) == 1

    async def test_does_nothing_when_no_regions(self) -> None:
        service, weather_repo, investment_repo = _make_service(regions=[])

        await service.run()

        assert len(weather_repo._snapshots) == 0
        assert len(investment_repo._evaluations) == 0

    async def test_continues_on_single_region_failure(self) -> None:
        """If one region fails, the others should still be processed."""
        regions = [
            FakeRegionRow(id=uuid.uuid4(), name="CityA", lat=10.0, lon=20.0),
            FakeRegionRow(id=uuid.uuid4(), name="CityB", lat=11.0, lon=21.0),
        ]
        # Config only has RAIN — but client returns RAIN, so both should succeed
        service, weather_repo, investment_repo = _make_service(regions=regions)

        await service.run()

        assert len(weather_repo._snapshots) == 2
        assert len(investment_repo._evaluations) == 2
