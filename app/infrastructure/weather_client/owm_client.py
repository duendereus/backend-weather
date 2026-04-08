import logging

import httpx

from app.core.config import settings
from app.core.exceptions import WeatherServiceUnavailableError
from app.domain.enums import WeatherCondition
from app.domain.schemas.weather import WeatherData
from app.infrastructure.weather_client.base import WeatherClient

logger = logging.getLogger(__name__)

# OWM "main" field → our enum.  Anything not listed falls to EXTREME.
_OWM_CONDITION_MAP: dict[str, WeatherCondition] = {
    "Clear": WeatherCondition.CLEAR,
    "Clouds": WeatherCondition.CLOUDS,
    "Drizzle": WeatherCondition.DRIZZLE,
    "Rain": WeatherCondition.RAIN,
    "Thunderstorm": WeatherCondition.THUNDERSTORM,
    "Snow": WeatherCondition.SNOW,
}


class OWMClient(WeatherClient):
    """Real implementation that calls the OpenWeatherMap Current Weather API."""

    def __init__(self) -> None:
        self._base_url = settings.OWM_BASE_URL
        self._api_key = settings.OWM_API_KEY
        self._timeout = settings.OWM_TIMEOUT_SECONDS

    async def get_current_weather(
        self,
        *,
        city: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
    ) -> WeatherData:
        params: dict[str, str | float] = {
            "appid": self._api_key,
            "units": "metric",
        }
        if city is not None:
            params["q"] = city
        else:
            assert lat is not None and lon is not None
            params["lat"] = lat
            params["lon"] = lon

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(f"{self._base_url}/weather", params=params)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("OWM request failed: %s", exc)
            if exc.response.status_code == 401:
                msg = "API key de OpenWeatherMap invalida o aun no activada (puede tardar hasta 2 horas)"
            elif exc.response.status_code == 404:
                msg = "Ciudad no encontrada en OpenWeatherMap"
            else:
                msg = f"OpenWeatherMap respondio con error {exc.response.status_code}"
            raise WeatherServiceUnavailableError(msg) from exc
        except httpx.HTTPError as exc:
            logger.error("OWM network error: %s", exc)
            raise WeatherServiceUnavailableError(
                "No se pudo conectar con OpenWeatherMap. Intenta de nuevo en unos minutos."
            ) from exc

        data = response.json()
        return self._parse_response(data)

    @staticmethod
    def _parse_response(data: dict) -> WeatherData:  # type: ignore[type-arg]
        weather_block = data["weather"][0]
        owm_main: str = weather_block["main"]
        condition = _OWM_CONDITION_MAP.get(owm_main, WeatherCondition.EXTREME)

        return WeatherData(
            condition=condition,
            description=weather_block.get("description", owm_main.lower()),
            temperature_c=data["main"]["temp"],
            wind_speed_ms=data["wind"]["speed"],
            city_name=data.get("name", "Unknown"),
            lat=data["coord"]["lat"],
            lon=data["coord"]["lon"],
        )
