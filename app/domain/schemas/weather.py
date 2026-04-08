from pydantic import BaseModel

from app.domain.enums import WeatherCondition


class WeatherData(BaseModel):
    """Internal schema returned by WeatherClient implementations."""

    condition: WeatherCondition
    description: str
    temperature_c: float
    wind_speed_ms: float
    city_name: str
    lat: float
    lon: float
