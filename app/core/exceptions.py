class WeatherServiceUnavailableError(Exception):
    """OpenWeatherMap API is unreachable or returned an error."""


class RegionNotFoundError(Exception):
    """The requested region does not exist."""


class IncentiveConfigNotFoundError(Exception):
    """No incentive configuration found for the given weather condition."""
