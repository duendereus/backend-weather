import uuid

import pytest

from app.domain.enums import InvestmentLevel, WeatherCondition
from app.services.investment_service import InvestmentService
from tests.fakes import FakeConfigRepository, FakeInvestmentRepository


def _make_service(
    pct_map: dict[WeatherCondition, float],
    base_fare: float = 120.0,
) -> InvestmentService:
    return InvestmentService(
        config_repo=FakeConfigRepository(
            incentive_pct_by_condition=pct_map,
            base_fare=base_fare,
        ),
        investment_repo=FakeInvestmentRepository(),
    )


# ---------------------------------------------------------------------------
# Condition → InvestmentLevel mapping
# ---------------------------------------------------------------------------


class TestInvestmentLevelMapping:
    async def test_clear_returns_none_level(self) -> None:
        service = _make_service({WeatherCondition.CLEAR: 0.0})
        result = await service.calculate(
            condition=WeatherCondition.CLEAR,
            region_id=uuid.uuid4(),
            snapshot_id=uuid.uuid4(),
        )
        assert result.investment_level == InvestmentLevel.NONE

    async def test_clouds_returns_minimal_level(self) -> None:
        service = _make_service({WeatherCondition.CLOUDS: 5.0})
        result = await service.calculate(
            condition=WeatherCondition.CLOUDS,
            region_id=uuid.uuid4(),
            snapshot_id=uuid.uuid4(),
        )
        assert result.investment_level == InvestmentLevel.MINIMAL

    async def test_drizzle_returns_low_level(self) -> None:
        service = _make_service({WeatherCondition.DRIZZLE: 15.0})
        result = await service.calculate(
            condition=WeatherCondition.DRIZZLE,
            region_id=uuid.uuid4(),
            snapshot_id=uuid.uuid4(),
        )
        assert result.investment_level == InvestmentLevel.LOW

    async def test_rain_returns_medium_level(self) -> None:
        service = _make_service({WeatherCondition.RAIN: 35.0})
        result = await service.calculate(
            condition=WeatherCondition.RAIN,
            region_id=uuid.uuid4(),
            snapshot_id=uuid.uuid4(),
        )
        assert result.investment_level == InvestmentLevel.MEDIUM

    async def test_thunderstorm_returns_high_level(self) -> None:
        service = _make_service({WeatherCondition.THUNDERSTORM: 60.0})
        result = await service.calculate(
            condition=WeatherCondition.THUNDERSTORM,
            region_id=uuid.uuid4(),
            snapshot_id=uuid.uuid4(),
        )
        assert result.investment_level == InvestmentLevel.HIGH

    async def test_snow_returns_high_level(self) -> None:
        service = _make_service({WeatherCondition.SNOW: 60.0})
        result = await service.calculate(
            condition=WeatherCondition.SNOW,
            region_id=uuid.uuid4(),
            snapshot_id=uuid.uuid4(),
        )
        assert result.investment_level == InvestmentLevel.HIGH

    async def test_extreme_returns_critical_level(self) -> None:
        service = _make_service({WeatherCondition.EXTREME: 100.0})
        result = await service.calculate(
            condition=WeatherCondition.EXTREME,
            region_id=uuid.uuid4(),
            snapshot_id=uuid.uuid4(),
        )
        assert result.investment_level == InvestmentLevel.CRITICAL


# ---------------------------------------------------------------------------
# Investment calculation
# ---------------------------------------------------------------------------


class TestInvestmentCalculation:
    async def test_total_investment_formula(self) -> None:
        """total = base_fare × (1 + incentive_pct / 100)"""
        service = _make_service({WeatherCondition.RAIN: 35.0}, base_fare=120.0)
        result = await service.calculate(
            condition=WeatherCondition.RAIN,
            region_id=uuid.uuid4(),
            snapshot_id=uuid.uuid4(),
        )
        assert result.incentive_pct == 35.0
        assert result.base_fare == 120.0
        assert result.incentive_amt == pytest.approx(42.0)
        assert result.total_investment == pytest.approx(162.0)

    async def test_zero_incentive_on_clear(self) -> None:
        service = _make_service({WeatherCondition.CLEAR: 0.0}, base_fare=100.0)
        result = await service.calculate(
            condition=WeatherCondition.CLEAR,
            region_id=uuid.uuid4(),
            snapshot_id=uuid.uuid4(),
        )
        assert result.incentive_amt == 0.0
        assert result.total_investment == 100.0

    async def test_full_incentive_on_extreme(self) -> None:
        service = _make_service({WeatherCondition.EXTREME: 100.0}, base_fare=200.0)
        result = await service.calculate(
            condition=WeatherCondition.EXTREME,
            region_id=uuid.uuid4(),
            snapshot_id=uuid.uuid4(),
        )
        assert result.incentive_amt == pytest.approx(200.0)
        assert result.total_investment == pytest.approx(400.0)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


class TestInvestmentPersistence:
    async def test_saves_evaluation(self) -> None:
        investment_repo = FakeInvestmentRepository()
        service = InvestmentService(
            config_repo=FakeConfigRepository(
                incentive_pct_by_condition={WeatherCondition.RAIN: 35.0},
                base_fare=120.0,
            ),
            investment_repo=investment_repo,
        )

        await service.calculate(
            condition=WeatherCondition.RAIN,
            region_id=uuid.uuid4(),
            snapshot_id=uuid.uuid4(),
        )

        assert len(investment_repo._evaluations) == 1


# ---------------------------------------------------------------------------
# Missing config
# ---------------------------------------------------------------------------


class TestInvestmentMissingConfig:
    async def test_raises_when_no_config_for_condition(self) -> None:
        service = _make_service({})  # empty config
        from app.core.exceptions import IncentiveConfigNotFoundError

        with pytest.raises(IncentiveConfigNotFoundError):
            await service.calculate(
                condition=WeatherCondition.RAIN,
                region_id=uuid.uuid4(),
                snapshot_id=uuid.uuid4(),
            )
