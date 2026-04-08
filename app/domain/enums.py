from enum import Enum


class WeatherCondition(str, Enum):
    CLEAR = "CLEAR"
    CLOUDS = "CLOUDS"
    DRIZZLE = "DRIZZLE"
    RAIN = "RAIN"
    THUNDERSTORM = "THUNDERSTORM"
    SNOW = "SNOW"
    EXTREME = "EXTREME"


class InvestmentLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
