import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import WeatherCondition


class RegionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class RegionResponse(BaseModel):
    id: uuid.UUID
    name: str
    lat: float
    lon: float
    created_at: datetime


class SnapshotResponse(BaseModel):
    id: uuid.UUID
    region_id: uuid.UUID
    condition: WeatherCondition
    description: str
    temperature_c: float
    wind_speed_ms: float
    queried_at: datetime
