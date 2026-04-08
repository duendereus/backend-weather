import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import WeatherCondition


class RegionCreateRequest(BaseModel):
    """Registrar una nueva region geografica para monitoreo climatico.

    El nombre debe coincidir con el que reconoce OpenWeatherMap
    (ej. 'Mexico City' en lugar de 'CDMX').
    """

    model_config = {"json_schema_extra": {
        "examples": [{"name": "Guadalajara", "lat": 20.6597, "lon": -103.3496}]
    }}

    name: str = Field(
        min_length=1,
        max_length=255,
        description="Nombre unico de la region o ciudad.",
    )
    lat: float = Field(
        ge=-90,
        le=90,
        description="Latitud (-90 a 90).",
    )
    lon: float = Field(
        ge=-180,
        le=180,
        description="Longitud (-180 a 180).",
    )


class RegionResponse(BaseModel):
    """Region registrada en el sistema."""

    id: uuid.UUID = Field(description="Identificador unico de la region.")
    name: str = Field(description="Nombre de la region.")
    lat: float = Field(description="Latitud.")
    lon: float = Field(description="Longitud.")
    created_at: datetime = Field(description="Fecha de creacion (UTC).")


class SnapshotResponse(BaseModel):
    """Snapshot de clima capturado para una region.

    Los snapshots se generan automaticamente por el scheduler cada N minutos,
    o cuando se realiza una evaluacion de inversion.
    """

    id: uuid.UUID = Field(description="Identificador unico del snapshot.")
    region_id: uuid.UUID = Field(description="Region asociada.")
    condition: WeatherCondition = Field(description="Condicion climatica detectada.")
    description: str = Field(description="Descripcion del clima (ej. 'light rain').")
    temperature_c: float = Field(description="Temperatura en grados Celsius.")
    wind_speed_ms: float = Field(description="Velocidad del viento en m/s.")
    queried_at: datetime = Field(description="Momento de la consulta a OpenWeatherMap (UTC).")
