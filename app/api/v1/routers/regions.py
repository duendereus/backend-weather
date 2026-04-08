import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_region_repo, get_weather_repo
from app.domain.enums import WeatherCondition
from app.domain.models.region import Region
from app.domain.schemas.regions import RegionCreateRequest, RegionResponse, SnapshotResponse
from app.repositories.region_repository import RegionRepository
from app.repositories.weather_repository import WeatherRepository

router = APIRouter(prefix="/regions", tags=["regions"])


@router.get(
    "",
    response_model=list[RegionResponse],
    summary="Listar regiones registradas",
    description="Retorna todas las regiones geograficas registradas, ordenadas alfabeticamente.",
)
async def list_regions(
    region_repo: RegionRepository = Depends(get_region_repo),
) -> list[RegionResponse]:
    regions = await region_repo.get_all()
    return [
        RegionResponse(
            id=r.id,
            name=r.name,
            lat=r.lat,
            lon=r.lon,
            created_at=r.created_at,
        )
        for r in regions
    ]


@router.post(
    "",
    response_model=RegionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una nueva region",
    description="""
Registra una region geografica para monitoreo climatico. El scheduler
consultara el clima de esta region periodicamente y generara snapshots
automaticos.

**Importante:** el nombre debe coincidir con el que reconoce OpenWeatherMap
(ej. `Mexico City` en lugar de `CDMX`). Si el nombre no es reconocido,
las evaluaciones para esta region fallaran.

Retorna **409 Conflict** si ya existe una region con el mismo nombre.
""",
    responses={
        201: {"description": "Region creada exitosamente."},
        409: {"description": "Ya existe una region con ese nombre."},
        422: {"description": "Datos invalidos."},
    },
)
async def create_region(
    body: RegionCreateRequest,
    region_repo: RegionRepository = Depends(get_region_repo),
) -> RegionResponse:
    existing = await region_repo.get_by_name(body.name)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Region '{body.name}' already exists",
        )
    region = Region(name=body.name, lat=body.lat, lon=body.lon)
    created = await region_repo.create(region)
    return RegionResponse(
        id=created.id,
        name=created.name,
        lat=created.lat,
        lon=created.lon,
        created_at=created.created_at,
    )


@router.delete(
    "/{region_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una region",
    description="""
Elimina una region y todos sus datos asociados (snapshots de clima
y evaluaciones de inversion). Esta accion es irreversible.
""",
    responses={
        204: {"description": "Region eliminada exitosamente."},
        404: {"description": "Region no encontrada."},
    },
)
async def delete_region(
    region_id: uuid.UUID,
    region_repo: RegionRepository = Depends(get_region_repo),
) -> None:
    region = await region_repo.get_by_id(region_id)
    if region is None:
        raise HTTPException(status_code=404, detail="Region not found")
    await region_repo.delete(region)


@router.get(
    "/{region_id}/snapshots",
    response_model=list[SnapshotResponse],
    summary="Snapshots de clima de una region",
    description="""
Retorna los snapshots de clima capturados para una region, ordenados
del mas reciente al mas antiguo. Los snapshots se generan automaticamente
por el scheduler o cuando se realiza una evaluacion.

Soporta paginacion con `limit` y `offset`.
""",
    responses={
        200: {"description": "Lista de snapshots (puede estar vacia)."},
        404: {"description": "Region no encontrada."},
    },
)
async def list_snapshots(
    region_id: uuid.UUID,
    limit: int = Query(
        default=50, ge=1, le=200,
        description="Cantidad maxima de resultados (1-200).",
    ),
    offset: int = Query(
        default=0, ge=0,
        description="Cantidad de resultados a saltar.",
    ),
    region_repo: RegionRepository = Depends(get_region_repo),
    weather_repo: WeatherRepository = Depends(get_weather_repo),
) -> list[SnapshotResponse]:
    region = await region_repo.get_by_id(region_id)
    if region is None:
        raise HTTPException(status_code=404, detail="Region not found")
    snapshots = await weather_repo.get_by_region(region_id, limit=limit, offset=offset)
    return [
        SnapshotResponse(
            id=s.id,
            region_id=s.region_id,
            condition=WeatherCondition(s.condition),
            description=s.description,
            temperature_c=s.temperature_c,
            wind_speed_ms=s.wind_speed_ms,
            queried_at=s.queried_at,
        )
        for s in snapshots
    ]
