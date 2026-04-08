import pytest

from app.domain.enums import WeatherCondition
from app.infrastructure.weather_client.owm_client import OWMClient


def _make_owm_response(main: str = "Rain", description: str = "moderate rain") -> dict:  # type: ignore[type-arg]
    return {
        "coord": {"lat": 20.66, "lon": -103.35},
        "weather": [{"main": main, "description": description}],
        "main": {"temp": 18.4},
        "wind": {"speed": 3.2},
        "name": "Guadalajara",
    }


class TestOWMClientParseResponse:
    @pytest.mark.parametrize(
        ("owm_main", "expected"),
        [
            ("Clear", WeatherCondition.CLEAR),
            ("Clouds", WeatherCondition.CLOUDS),
            ("Drizzle", WeatherCondition.DRIZZLE),
            ("Rain", WeatherCondition.RAIN),
            ("Thunderstorm", WeatherCondition.THUNDERSTORM),
            ("Snow", WeatherCondition.SNOW),
        ],
    )
    def test_maps_known_conditions(self, owm_main: str, expected: WeatherCondition) -> None:
        data = _make_owm_response(main=owm_main)
        result = OWMClient._parse_response(data)
        assert result.condition == expected

    def test_maps_unknown_condition_to_extreme(self) -> None:
        data = _make_owm_response(main="Tornado")
        result = OWMClient._parse_response(data)
        assert result.condition == WeatherCondition.EXTREME

    def test_parses_numeric_fields(self) -> None:
        data = _make_owm_response()
        result = OWMClient._parse_response(data)
        assert result.temperature_c == 18.4
        assert result.wind_speed_ms == 3.2
        assert result.city_name == "Guadalajara"
        assert result.lat == 20.66
        assert result.lon == -103.35
