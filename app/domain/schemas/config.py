from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import WeatherCondition


class IncentiveConfigResponse(BaseModel):
    condition: WeatherCondition
    base_fare: float
    incentive_pct: float
    updated_at: datetime


class IncentiveConfigUpdateRequest(BaseModel):
    base_fare: float = Field(gt=0)
    incentive_pct: float = Field(ge=0, le=100)
