from abc import ABC, abstractmethod

from app.domain.schemas.weather import WeatherData


class WeatherClient(ABC):
    @abstractmethod
    async def get_current_weather(
        self,
        *,
        city: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
    ) -> WeatherData:
        """Fetch current weather for a location (by city name or coordinates)."""
