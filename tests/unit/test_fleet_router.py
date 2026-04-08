import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_investment_service, get_weather_service
from app.domain.enums import InvestmentLevel, WeatherCondition
from app.main import app
from app.services.investment_service import InvestmentResult
from app.services.weather_service import WeatherResult


class FakeWeatherServiceForRouter:
    def __init__(self, condition: WeatherCondition = WeatherCondition.RAIN) -> None:
        self._condition = condition
        self._region_id = uuid.uuid4()
        self._snapshot_id = uuid.uuid4()

    async def get_weather(
        self, *, city: str | None = None, lat: float | None = None, lon: float | None = None
    ) -> WeatherResult:
        return WeatherResult(
            condition=self._condition,
            description="moderate rain",
            temperature_c=18.0,
            wind_speed_ms=3.5,
            city_name=city or "TestCity",
            region_id=self._region_id,
            snapshot_id=self._snapshot_id,
        )


class FakeInvestmentServiceForRouter:
    async def calculate(
        self, *, condition: WeatherCondition, region_id: uuid.UUID, snapshot_id: uuid.UUID
    ) -> InvestmentResult:
        return InvestmentResult(
            investment_level=InvestmentLevel.MEDIUM,
            base_fare=120.0,
            incentive_pct=35.0,
            incentive_amt=42.0,
            total_investment=162.0,
            evaluated_at=datetime.now(timezone.utc),
        )


@pytest.fixture
def _override_deps():  # type: ignore[no-untyped-def]
    app.dependency_overrides[get_weather_service] = FakeWeatherServiceForRouter
    app.dependency_overrides[get_investment_service] = FakeInvestmentServiceForRouter
    yield
    app.dependency_overrides.clear()


class TestFleetEvaluateEndpoint:
    @pytest.mark.usefixtures("_override_deps")
    async def test_evaluate_with_city(self) -> None:
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/fleet/evaluate",
                json={"city": "Guadalajara"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["condition"] == "RAIN"
        assert data["investment_level"] == "MEDIUM"
        assert data["total_investment"] == 162.0
        assert data["region"] == "Guadalajara"

    @pytest.mark.usefixtures("_override_deps")
    async def test_evaluate_with_coordinates(self) -> None:
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/fleet/evaluate",
                json={"lat": 20.66, "lon": -103.35},
            )

        assert response.status_code == 200

    async def test_evaluate_rejects_empty_body(self) -> None:
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/fleet/evaluate", json={})

        assert response.status_code == 422

    async def test_evaluate_rejects_city_and_coords(self) -> None:
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/fleet/evaluate",
                json={"city": "Bogota", "lat": 4.71, "lon": -74.07},
            )

        assert response.status_code == 422
