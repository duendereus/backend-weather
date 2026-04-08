from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import InvestmentLevel, WeatherCondition


class FleetEvaluateRequest(BaseModel):
    """Solicitud de evaluacion de inversion en flota.

    Enviar **ciudad** (por nombre) o **coordenadas** (lat + lon), nunca ambos.
    """

    model_config = {"json_schema_extra": {
        "examples": [
            {"city": "Guadalajara"},
            {"lat": 20.6597, "lon": -103.3496},
        ]
    }}

    city: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Nombre de la ciudad a evaluar. Debe coincidir con el nombre "
        "reconocido por OpenWeatherMap (ej. 'Mexico City', no 'CDMX').",
    )
    lat: float | None = Field(
        default=None,
        ge=-90,
        le=90,
        description="Latitud de la ubicacion (-90 a 90).",
    )
    lon: float | None = Field(
        default=None,
        ge=-180,
        le=180,
        description="Longitud de la ubicacion (-180 a 180).",
    )

    def model_post_init(self, __context: object) -> None:
        has_city = self.city is not None
        has_coords = self.lat is not None and self.lon is not None
        if not has_city and not has_coords:
            raise ValueError("Either 'city' or both 'lat' and 'lon' must be provided")
        if has_city and has_coords:
            raise ValueError("Provide 'city' or 'lat'/'lon', not both")


class FleetEvaluateResponse(BaseModel):
    """Resultado de la evaluacion de inversion en flota.

    Contiene la informacion climatica, el nivel de inversion calculado
    y el desglose economico (tarifa base, incentivo, total).
    """

    model_config = {"json_schema_extra": {
        "examples": [{
            "region": "Guadalajara",
            "condition": "RAIN",
            "description": "moderate rain",
            "temperature_c": 18.4,
            "wind_speed_ms": 3.2,
            "investment_level": "MEDIUM",
            "base_fare": 120.0,
            "incentive_pct": 35.0,
            "incentive_amt": 42.0,
            "total_investment": 162.0,
            "evaluated_at": "2026-04-08T14:32:00Z",
        }]
    }}

    region: str = Field(description="Nombre de la ciudad o region evaluada.")
    condition: WeatherCondition = Field(
        description="Condicion climatica detectada por OpenWeatherMap."
    )
    description: str = Field(
        description="Descripcion detallada del clima (ej. 'moderate rain')."
    )
    temperature_c: float = Field(description="Temperatura actual en grados Celsius.")
    wind_speed_ms: float = Field(description="Velocidad del viento en metros por segundo.")
    investment_level: InvestmentLevel = Field(
        description="Nivel de inversion calculado: NONE, MINIMAL, LOW, MEDIUM, HIGH o CRITICAL."
    )
    base_fare: float = Field(description="Tarifa base configurada para esta condicion ($).")
    incentive_pct: float = Field(description="Porcentaje de incentivo aplicado (0-100).")
    incentive_amt: float = Field(
        description="Monto del incentivo en dolares: base_fare x (incentive_pct / 100)."
    )
    total_investment: float = Field(
        description="Inversion total: base_fare + incentive_amt."
    )
    evaluated_at: datetime = Field(description="Fecha y hora UTC de la evaluacion.")
