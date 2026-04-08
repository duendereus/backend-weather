import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domain.enums import InvestmentLevel, WeatherCondition
from app.domain.schemas.config import IncentiveConfigResponse, IncentiveConfigUpdateRequest
from app.domain.schemas.fleet import FleetEvaluateRequest, FleetEvaluateResponse
from app.domain.schemas.regions import RegionCreateRequest, RegionResponse, SnapshotResponse

# ---------------------------------------------------------------------------
# FleetEvaluateRequest
# ---------------------------------------------------------------------------


class TestFleetEvaluateRequest:
    def test_valid_with_city(self) -> None:
        req = FleetEvaluateRequest(city="Guadalajara")
        assert req.city == "Guadalajara"
        assert req.lat is None

    def test_valid_with_coordinates(self) -> None:
        req = FleetEvaluateRequest(lat=20.66, lon=-103.35)
        assert req.lat == 20.66
        assert req.city is None

    def test_rejects_empty_body(self) -> None:
        with pytest.raises(ValidationError):
            FleetEvaluateRequest()

    def test_rejects_city_and_coords_together(self) -> None:
        with pytest.raises(ValidationError):
            FleetEvaluateRequest(city="Bogota", lat=4.71, lon=-74.07)

    def test_rejects_partial_coords(self) -> None:
        with pytest.raises(ValidationError):
            FleetEvaluateRequest(lat=20.66)

    def test_rejects_lat_out_of_range(self) -> None:
        with pytest.raises(ValidationError):
            FleetEvaluateRequest(lat=91.0, lon=0.0)

    def test_rejects_lon_out_of_range(self) -> None:
        with pytest.raises(ValidationError):
            FleetEvaluateRequest(lat=0.0, lon=181.0)


# ---------------------------------------------------------------------------
# FleetEvaluateResponse
# ---------------------------------------------------------------------------


class TestFleetEvaluateResponse:
    def test_valid_response(self) -> None:
        resp = FleetEvaluateResponse(
            region="Guadalajara",
            condition=WeatherCondition.RAIN,
            description="moderate rain",
            temperature_c=18.4,
            wind_speed_ms=3.2,
            investment_level=InvestmentLevel.MEDIUM,
            base_fare=120.00,
            incentive_pct=35.0,
            incentive_amt=42.00,
            total_investment=162.00,
            evaluated_at=datetime.now(UTC),
        )
        assert resp.condition == WeatherCondition.RAIN
        assert resp.investment_level == InvestmentLevel.MEDIUM


# ---------------------------------------------------------------------------
# IncentiveConfigUpdateRequest
# ---------------------------------------------------------------------------


class TestIncentiveConfigUpdateRequest:
    def test_valid_update(self) -> None:
        req = IncentiveConfigUpdateRequest(base_fare=120.0, incentive_pct=40.0)
        assert req.base_fare == 120.0

    def test_rejects_negative_base_fare(self) -> None:
        with pytest.raises(ValidationError):
            IncentiveConfigUpdateRequest(base_fare=-10.0, incentive_pct=40.0)

    def test_rejects_pct_over_100(self) -> None:
        with pytest.raises(ValidationError):
            IncentiveConfigUpdateRequest(base_fare=100.0, incentive_pct=101.0)


# ---------------------------------------------------------------------------
# IncentiveConfigResponse
# ---------------------------------------------------------------------------


class TestIncentiveConfigResponse:
    def test_valid_response(self) -> None:
        resp = IncentiveConfigResponse(
            condition=WeatherCondition.RAIN,
            base_fare=120.0,
            incentive_pct=35.0,
            updated_at=datetime.now(UTC),
        )
        assert resp.condition == WeatherCondition.RAIN


# ---------------------------------------------------------------------------
# RegionCreateRequest
# ---------------------------------------------------------------------------


class TestRegionCreateRequest:
    def test_valid_region(self) -> None:
        req = RegionCreateRequest(name="CDMX", lat=19.43, lon=-99.13)
        assert req.name == "CDMX"

    def test_rejects_empty_name(self) -> None:
        with pytest.raises(ValidationError):
            RegionCreateRequest(name="", lat=19.43, lon=-99.13)


# ---------------------------------------------------------------------------
# RegionResponse
# ---------------------------------------------------------------------------


class TestRegionResponse:
    def test_valid_response(self) -> None:
        resp = RegionResponse(
            id=uuid.uuid4(),
            name="CDMX",
            lat=19.43,
            lon=-99.13,
            created_at=datetime.now(UTC),
        )
        assert resp.name == "CDMX"


# ---------------------------------------------------------------------------
# SnapshotResponse
# ---------------------------------------------------------------------------


class TestSnapshotResponse:
    def test_valid_response(self) -> None:
        resp = SnapshotResponse(
            id=uuid.uuid4(),
            region_id=uuid.uuid4(),
            condition=WeatherCondition.SNOW,
            description="light snow",
            temperature_c=-2.0,
            wind_speed_ms=5.1,
            queried_at=datetime.now(UTC),
        )
        assert resp.condition == WeatherCondition.SNOW
