import uuid

from fastapi import APIRouter, Depends

from app.api.deps import get_investment_repo, get_investment_service, get_weather_service
from app.domain.schemas.fleet import FleetEvaluateRequest, FleetEvaluateResponse
from app.repositories.investment_repository import InvestmentRepository
from app.services.investment_service import InvestmentService
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/fleet", tags=["fleet"])


@router.post("/evaluate", response_model=FleetEvaluateResponse)
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


@router.get("/history")
async def history(
    region_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
    investment_repo: InvestmentRepository = Depends(get_investment_repo),
) -> list[dict]:  # type: ignore[type-arg]
    evaluations = await investment_repo.get_history(
        region_id=region_id, limit=limit, offset=offset
    )
    return [
        {
            "id": str(e.id),
            "region_id": str(e.region_id),
            "investment_level": e.investment_level,
            "base_fare": e.base_fare,
            "incentive_pct": e.incentive_pct,
            "incentive_amt": e.incentive_amt,
            "total_investment": e.total_investment,
            "evaluated_at": str(e.evaluated_at),
        }
        for e in evaluations
    ]
