from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import InvestmentLevel, WeatherCondition


class FleetEvaluateRequest(BaseModel):
    city: str | None = Field(default=None, min_length=1, max_length=255)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)

    def model_post_init(self, __context: object) -> None:
        has_city = self.city is not None
        has_coords = self.lat is not None and self.lon is not None
        if not has_city and not has_coords:
            raise ValueError("Either 'city' or both 'lat' and 'lon' must be provided")
        if has_city and has_coords:
            raise ValueError("Provide 'city' or 'lat'/'lon', not both")


class FleetEvaluateResponse(BaseModel):
    region: str
    condition: WeatherCondition
    description: str
    temperature_c: float
    wind_speed_ms: float
    investment_level: InvestmentLevel
    base_fare: float
    incentive_pct: float
    incentive_amt: float
    total_investment: float
    evaluated_at: datetime
