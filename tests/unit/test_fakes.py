import pytest

from app.domain.enums import WeatherCondition
from app.domain.schemas.weather import WeatherData
from app.infrastructure.weather_client.base import WeatherClient
from tests.fakes import FakeWeatherClient


class TestFakeWeatherClient:
    def test_is_instance_of_abc(self) -> None:
        fake = FakeWeatherClient()
        assert isinstance(fake, WeatherClient)

    @pytest.mark.asyncio
    async def test_returns_configured_weather(self) -> None:
        fake = FakeWeatherClient(condition=WeatherCondition.RAIN, city_name="Bogota")
        result = await fake.get_current_weather(city="Bogota")
        assert isinstance(result, WeatherData)
        assert result.condition == WeatherCondition.RAIN
        assert result.city_name == "Bogota"
