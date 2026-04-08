import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_region_repo, get_weather_repo
from app.domain.enums import WeatherCondition
from app.main import app
from tests.fakes import FakeRegionRepository, FakeRegionRow, FakeSnapshotRow, FakeWeatherRepository


@pytest.fixture
def region_repo() -> FakeRegionRepository:
    return FakeRegionRepository(
        regions=[
            FakeRegionRow(id=uuid.uuid4(), name="Guadalajara", lat=20.66, lon=-103.35),
            FakeRegionRow(id=uuid.uuid4(), name="Bogota", lat=4.71, lon=-74.07),
        ]
    )


@pytest.fixture
def weather_repo() -> FakeWeatherRepository:
    return FakeWeatherRepository()


@pytest.fixture
def _override_repos(region_repo: FakeRegionRepository, weather_repo: FakeWeatherRepository):  # type: ignore[no-untyped-def]
    app.dependency_overrides[get_region_repo] = lambda: region_repo
    app.dependency_overrides[get_weather_repo] = lambda: weather_repo
    yield
    app.dependency_overrides.clear()


class TestRegionsEndpoints:
    @pytest.mark.usefixtures("_override_repos")
    async def test_list_regions(self) -> None:
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/regions")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        names = {r["name"] for r in data}
        assert "Guadalajara" in names

    @pytest.mark.usefixtures("_override_repos")
    async def test_create_region(self) -> None:
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/regions",
                json={"name": "CDMX", "lat": 19.43, "lon": -99.13},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "CDMX"

    @pytest.mark.usefixtures("_override_repos")
    async def test_create_duplicate_region_returns_409(self) -> None:
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/regions",
                json={"name": "Guadalajara", "lat": 20.66, "lon": -103.35},
            )

        assert response.status_code == 409

    @pytest.mark.usefixtures("_override_repos")
    async def test_list_snapshots_for_region(
        self, region_repo: FakeRegionRepository, weather_repo: FakeWeatherRepository
    ) -> None:
        region = region_repo._regions[0]
        weather_repo._snapshots.append(
            FakeSnapshotRow(
                id=uuid.uuid4(),
                region_id=region.id,
                condition=WeatherCondition.RAIN.value,
                description="light rain",
                temperature_c=17.0,
                wind_speed_ms=4.0,
            )
        )

        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/regions/{region.id}/snapshots")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["condition"] == "RAIN"

    @pytest.mark.usefixtures("_override_repos")
    async def test_snapshots_for_unknown_region_returns_404(self) -> None:
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/regions/{uuid.uuid4()}/snapshots")

        assert response.status_code == 404
