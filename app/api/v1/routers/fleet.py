import uuid

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_investment_repo, get_investment_service, get_weather_service
from app.domain.schemas.fleet import FleetEvaluateRequest, FleetEvaluateResponse
from app.repositories.investment_repository import InvestmentRepository
from app.services.investment_service import InvestmentService
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/fleet", tags=["fleet"])


@router.post(
    "/evaluate",
    response_model=FleetEvaluateResponse,
    summary="Evaluar inversion en flota para una ubicacion",
    description="""
Consulta el clima actual de una ciudad (por nombre) o coordenadas (lat/lon)
y calcula el nivel de inversion economica que Rappi debe destinar a la flota
de repartidores en esa region.

**Flujo interno:**
1. Consulta OpenWeatherMap para obtener la condicion climatica actual.
2. Registra la region automaticamente si no existe.
3. Persiste un snapshot del clima.
4. Calcula el incentivo aplicando el porcentaje configurado sobre la tarifa base.

**Errores posibles:**
- `422`: Datos de entrada invalidos (ciudad vacia, coordenadas fuera de rango, etc.).
- `404`: No hay configuracion de incentivos para la condicion climatica detectada.
- `503`: No se pudo conectar con OpenWeatherMap (API caida o key invalida).
""",
    responses={
        200: {"description": "Evaluacion completada exitosamente."},
        404: {"description": "No hay configuracion de incentivos para la condicion detectada."},
        422: {"description": "Datos de entrada invalidos."},
        503: {"description": "OpenWeatherMap no disponible."},
    },
)
async def evaluate(
    body: FleetEvaluateRequest,
    weather_service: WeatherService = Depends(get_weather_service),
    investment_service: InvestmentService = Depends(get_investment_service),
) -> FleetEvaluateResponse:
    weather = await weather_service.get_weather(
        city=body.city, lat=body.lat, lon=body.lon
    )
    result = await investment_service.calculate(
        condition=weather.condition,
        region_id=weather.region_id,
        snapshot_id=weather.snapshot_id,
    )
    return FleetEvaluateResponse(
        region=weather.city_name,
        condition=weather.condition,
        description=weather.description,
        temperature_c=weather.temperature_c,
        wind_speed_ms=weather.wind_speed_ms,
        investment_level=result.investment_level,
        base_fare=result.base_fare,
        incentive_pct=result.incentive_pct,
        incentive_amt=result.incentive_amt,
        total_investment=result.total_investment,
        evaluated_at=result.evaluated_at,
    )


@router.get(
    "/history",
    summary="Historial de evaluaciones de inversion",
    description="""
Retorna las evaluaciones de inversion realizadas, ordenadas de la mas reciente
a la mas antigua. Soporta paginacion y filtro por region.
""",
    responses={
        200: {"description": "Lista de evaluaciones (puede estar vacia)."},
    },
)
async def history(
    region_id: uuid.UUID | None = Query(
        default=None,
        description="Filtrar por ID de region. Si no se envia, retorna todas.",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Cantidad maxima de resultados (1-200).",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Cantidad de resultados a saltar (para paginacion).",
    ),
    investment_repo: InvestmentRepository = Depends(get_investment_repo),
) -> list[dict]:  # type: ignore[type-arg]
    evaluations = await investment_repo.get_history(
        region_id=region_id, limit=limit, offset=offset
    )
    return [
        {
            "id": str(e.id),
            "region_id": str(e.region_id),
            "region_name": e.region.name if e.region else "—",
            "investment_level": e.investment_level,
            "base_fare": e.base_fare,
            "incentive_pct": e.incentive_pct,
            "incentive_amt": e.incentive_amt,
            "total_investment": e.total_investment,
            "evaluated_at": str(e.evaluated_at),
        }
        for e in evaluations
    ]
