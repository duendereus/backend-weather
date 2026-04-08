from enum import StrEnum


class WeatherCondition(StrEnum):
    CLEAR = "CLEAR"
    CLOUDS = "CLOUDS"
    DRIZZLE = "DRIZZLE"
    RAIN = "RAIN"
    THUNDERSTORM = "THUNDERSTORM"
    SNOW = "SNOW"
    EXTREME = "EXTREME"


class InvestmentLevel(StrEnum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
