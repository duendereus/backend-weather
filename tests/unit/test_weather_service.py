import uuid

import pytest

from app.domain.enums import WeatherCondition
from app.services.weather_service import WeatherService
from tests.fakes import FakeRegionRepository, FakeRegionRow, FakeWeatherClient, FakeWeatherRepository


class TestWeatherServiceGetWeather:
    async def test_returns_weather_data_for_city(self) -> None:
        client = FakeWeatherClient(
            condition=WeatherCondition.RAIN,
            description="moderate rain",
            temperature_c=18.0,
            wind_speed_ms=3.5,
            city_name="Guadalajara",
            lat=20.66,
            lon=-103.35,
        )
        weather_repo = FakeWeatherRepository()
        region_repo = FakeRegionRepository()
        service = WeatherService(
            weather_client=client,
            weather_repo=weather_repo,
            region_repo=region_repo,
        )

        result = await service.get_weather(city="Guadalajara")

        assert result.condition == WeatherCondition.RAIN
        assert result.temperature_c == 18.0
        assert result.city_name == "Guadalajara"

    async def test_returns_weather_data_for_coordinates(self) -> None:
        client = FakeWeatherClient(
            condition=WeatherCondition.SNOW,
            city_name="Ushuaia",
            lat=-54.8,
            lon=-68.3,
        )
        service = WeatherService(
            weather_client=client,
            weather_repo=FakeWeatherRepository(),
            region_repo=FakeRegionRepository(),
        )

        result = await service.get_weather(lat=-54.8, lon=-68.3)
        assert result.condition == WeatherCondition.SNOW

    async def test_persists_snapshot(self) -> None:
        client = FakeWeatherClient(condition=WeatherCondition.CLOUDS, city_name="Bogota")
        weather_repo = FakeWeatherRepository()
        region_repo = FakeRegionRepository()
        service = WeatherService(
            weather_client=client,
            weather_repo=weather_repo,
            region_repo=region_repo,
        )

        result = await service.get_weather(city="Bogota")

        assert len(weather_repo._snapshots) == 1
        snap = weather_repo._snapshots[0]
        assert snap.condition == WeatherCondition.CLOUDS.value

    async def test_creates_region_if_not_exists(self) -> None:
        client = FakeWeatherClient(
            condition=WeatherCondition.CLEAR, city_name="NuevaCity", lat=10.0, lon=20.0
        )
        region_repo = FakeRegionRepository()
        service = WeatherService(
            weather_client=client,
            weather_repo=FakeWeatherRepository(),
            region_repo=region_repo,
        )

        await service.get_weather(city="NuevaCity")

        assert len(region_repo._regions) == 1
        assert region_repo._regions[0].name == "NuevaCity"

    async def test_reuses_existing_region(self) -> None:
        existing = FakeRegionRow(
            id=uuid.uuid4(), name="Existente", lat=5.0, lon=-75.0
        )
        region_repo = FakeRegionRepository(regions=[existing])
        client = FakeWeatherClient(
            condition=WeatherCondition.CLEAR, city_name="Existente", lat=5.0, lon=-75.0
        )
        service = WeatherService(
            weather_client=client,
            weather_repo=FakeWeatherRepository(),
            region_repo=region_repo,
        )

        await service.get_weather(city="Existente")

        assert len(region_repo._regions) == 1  # no new region created

    async def test_result_includes_region_and_snapshot_ids(self) -> None:
        client = FakeWeatherClient(condition=WeatherCondition.RAIN, city_name="CDMX")
        service = WeatherService(
            weather_client=client,
            weather_repo=FakeWeatherRepository(),
            region_repo=FakeRegionRepository(),
        )

        result = await service.get_weather(city="CDMX")

        assert result.region_id is not None
        assert result.snapshot_id is not None
