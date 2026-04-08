from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

from app.core.exceptions import IncentiveConfigNotFoundError
from app.domain.enums import InvestmentLevel, WeatherCondition

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Condition → Level mapping (the percentages come from DB, only the level
# classification lives here)
# ---------------------------------------------------------------------------

_CONDITION_LEVEL_MAP: dict[WeatherCondition, InvestmentLevel] = {
    WeatherCondition.CLEAR: InvestmentLevel.NONE,
    WeatherCondition.CLOUDS: InvestmentLevel.NONE,
    WeatherCondition.DRIZZLE: InvestmentLevel.LOW,
    WeatherCondition.RAIN: InvestmentLevel.MEDIUM,
    WeatherCondition.THUNDERSTORM: InvestmentLevel.HIGH,
    WeatherCondition.SNOW: InvestmentLevel.HIGH,
    WeatherCondition.EXTREME: InvestmentLevel.CRITICAL,
}


# ---------------------------------------------------------------------------
# Protocols
# ---------------------------------------------------------------------------


class ConfigRepoProto(Protocol):
    async def get_by_condition(self, condition: WeatherCondition) -> Any: ...


class InvestmentRepoProto(Protocol):
    async def save_evaluation(self, evaluation: Any) -> Any: ...


# ---------------------------------------------------------------------------
# Result DTO
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InvestmentResult:
    investment_level: InvestmentLevel
    base_fare: float
    incentive_pct: float
    incentive_amt: float
    total_investment: float
    evaluated_at: datetime


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class InvestmentService:
    def __init__(
        self,
        *,
        config_repo: ConfigRepoProto,
        investment_repo: InvestmentRepoProto,
    ) -> None:
        self._config_repo = config_repo
        self._investment_repo = investment_repo

    async def calculate(
        self,
        *,
        condition: WeatherCondition,
        region_id: uuid.UUID,
        snapshot_id: uuid.UUID,
    ) -> InvestmentResult:
        config = await self._config_repo.get_by_condition(condition)
        if config is None:
            raise IncentiveConfigNotFoundError(
                f"No incentive config for condition {condition.value}"
            )

        base_fare: float = config.base_fare
        incentive_pct: float = config.incentive_pct
        incentive_amt = round(base_fare * incentive_pct / 100, 2)
        total_investment = round(base_fare + incentive_amt, 2)
        level = _CONDITION_LEVEL_MAP[condition]
        now = datetime.now(timezone.utc)

        # Persist
        from app.domain.models.investment_evaluation import InvestmentEvaluation

        evaluation = InvestmentEvaluation(
            snapshot_id=snapshot_id,
            region_id=region_id,
            investment_level=level.value,
            base_fare=base_fare,
            incentive_pct=incentive_pct,
            incentive_amt=incentive_amt,
            total_investment=total_investment,
        )
        await self._investment_repo.save_evaluation(evaluation)

        return InvestmentResult(
            investment_level=level,
            base_fare=base_fare,
            incentive_pct=incentive_pct,
            incentive_amt=incentive_amt,
            total_investment=total_investment,
            evaluated_at=now,
        )
