import inspect
from abc import ABC

import pytest

from app.domain.schemas.weather import WeatherData
from app.infrastructure.weather_client.base import WeatherClient


class TestWeatherClientABC:
    def test_is_abstract_class(self) -> None:
        assert issubclass(WeatherClient, ABC)

    def test_has_get_current_weather_method(self) -> None:
        assert hasattr(WeatherClient, "get_current_weather")

    def test_get_current_weather_is_async(self) -> None:
        method = WeatherClient.get_current_weather
        assert inspect.iscoroutinefunction(method)

    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            WeatherClient()  # type: ignore[abstract]


class TestWeatherData:
    def test_weather_data_schema_has_expected_fields(self) -> None:
        fields = set(WeatherData.model_fields.keys())
        expected = {
            "condition", "description", "temperature_c",
            "wind_speed_ms", "city_name", "lat", "lon",
        }
        assert fields == expected
