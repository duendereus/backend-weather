from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_config_repo
from app.domain.enums import WeatherCondition
from app.domain.schemas.config import IncentiveConfigResponse, IncentiveConfigUpdateRequest
from app.repositories.config_repository import ConfigRepository

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/incentive", response_model=list[IncentiveConfigResponse])
async def list_incentives(
    config_repo: ConfigRepository = Depends(get_config_repo),
) -> list[IncentiveConfigResponse]:
    configs = await config_repo.get_all()
    return [
        IncentiveConfigResponse(
            condition=WeatherCondition(c.condition),
            base_fare=c.base_fare,
            incentive_pct=c.incentive_pct,
            updated_at=c.updated_at,
        )
        for c in configs
    ]


@router.put("/incentive/{condition}", response_model=IncentiveConfigResponse)
async def update_incentive(
    condition: WeatherCondition,
    body: IncentiveConfigUpdateRequest,
    config_repo: ConfigRepository = Depends(get_config_repo),
) -> IncentiveConfigResponse:
    updated = await config_repo.update_by_condition(
        condition,
        base_fare=body.base_fare,
        incentive_pct=body.incentive_pct,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail=f"No config for {condition.value}")
    return IncentiveConfigResponse(
        condition=WeatherCondition(updated.condition),
        base_fare=updated.base_fare,
        incentive_pct=updated.incentive_pct,
        updated_at=updated.updated_at,
    )
