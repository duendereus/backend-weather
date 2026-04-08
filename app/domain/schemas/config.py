from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import WeatherCondition


class IncentiveConfigResponse(BaseModel):
    """Configuracion de incentivo para una condicion climatica."""

    condition: WeatherCondition = Field(description="Condicion climatica.")
    base_fare: float = Field(description="Tarifa base en dolares.")
    incentive_pct: float = Field(description="Porcentaje de incentivo (0-100).")
    updated_at: datetime = Field(description="Ultima actualizacion (UTC).")


class IncentiveConfigCreateRequest(BaseModel):
    """Crear una nueva configuracion de incentivo.

    Solo se permite una configuracion por condicion climatica.
    Si ya existe, devuelve 409 Conflict.
    """

    model_config = {"json_schema_extra": {
        "examples": [{"condition": "RAIN", "base_fare": 120.0, "incentive_pct": 35.0}]
    }}

    condition: WeatherCondition = Field(
        description="Condicion climatica: CLEAR, CLOUDS, DRIZZLE, RAIN, THUNDERSTORM, SNOW o EXTREME."
    )
    base_fare: float = Field(
        gt=0,
        description="Tarifa base en dolares. Debe ser mayor a 0.",
    )
    incentive_pct: float = Field(
        ge=0,
        le=100,
        description="Porcentaje de incentivo sobre la tarifa base (0 a 100).",
    )


class IncentiveConfigUpdateRequest(BaseModel):
    """Actualizar la tarifa base y/o porcentaje de incentivo de una condicion existente."""

    model_config = {"json_schema_extra": {
        "examples": [{"base_fare": 150.0, "incentive_pct": 40.0}]
    }}

    base_fare: float = Field(
        gt=0,
        description="Nueva tarifa base en dolares. Debe ser mayor a 0.",
    )
    incentive_pct: float = Field(
        ge=0,
        le=100,
        description="Nuevo porcentaje de incentivo (0 a 100).",
    )
