
import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_config_repo
from app.domain.enums import WeatherCondition
from app.main import app
from tests.fakes import FakeConfigRepository


@pytest.fixture
def config_repo() -> FakeConfigRepository:
    return FakeConfigRepository(
        incentive_pct_by_condition={
            WeatherCondition.CLEAR: 0.0,
            WeatherCondition.RAIN: 35.0,
            WeatherCondition.THUNDERSTORM: 60.0,
        },
        base_fare=120.0,
    )


@pytest.fixture
def _override_config_repo(config_repo: FakeConfigRepository):  # type: ignore[no-untyped-def]
    app.dependency_overrides[get_config_repo] = lambda: config_repo
    yield
    app.dependency_overrides.clear()


class TestConfigIncentiveEndpoints:
    @pytest.mark.usefixtures("_override_config_repo")
    async def test_list_incentives(self) -> None:
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/config/incentive")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        conditions = {item["condition"] for item in data}
        assert "RAIN" in conditions

    @pytest.mark.usefixtures("_override_config_repo")
    async def test_update_incentive(self) -> None:
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/api/v1/config/incentive/RAIN",
                json={"base_fare": 150.0, "incentive_pct": 40.0},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["base_fare"] == 150.0
        assert data["incentive_pct"] == 40.0

    @pytest.mark.usefixtures("_override_config_repo")
    async def test_update_incentive_not_found(self) -> None:
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/api/v1/config/incentive/EXTREME",
                json={"base_fare": 100.0, "incentive_pct": 100.0},
            )

        assert response.status_code == 404
