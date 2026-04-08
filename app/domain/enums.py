from enum import StrEnum


class WeatherCondition(StrEnum):
    CLEAR = "CLEAR"
    CLOUDS = "CLOUDS"
    DRIZZLE = "DRIZZLE"
    RAIN = "RAIN"
    THUNDERSTORM = "THUNDERSTORM"
    SNOW = "SNOW"
    EXTREME = "EXTREME"


class EvaluationSource(StrEnum):
    MANUAL = "MANUAL"
    SCHEDULED = "SCHEDULED"


class InvestmentLevel(StrEnum):
    NONE = "NONE"
    MINIMAL = "MINIMAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
