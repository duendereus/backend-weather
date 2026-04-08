import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.region import Region
from app.repositories.region_repository import RegionRepository


@pytest.mark.integration
class TestRegionRepository:
    async def test_create_and_get_by_id(self, db_session: AsyncSession) -> None:
        repo = RegionRepository(db_session)
        region = Region(name="Guadalajara", lat=20.66, lon=-103.35)

        created = await repo.create(region)

        assert created.id is not None
        assert created.name == "Guadalajara"

        fetched = await repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.name == "Guadalajara"

    async def test_get_by_name(self, db_session: AsyncSession) -> None:
        repo = RegionRepository(db_session)
        region = Region(name="Bogota", lat=4.71, lon=-74.07)
        await repo.create(region)

        fetched = await repo.get_by_name("Bogota")
        assert fetched is not None
        assert fetched.lat == 4.71

    async def test_get_by_name_returns_none_when_not_found(
        self, db_session: AsyncSession
    ) -> None:
        repo = RegionRepository(db_session)
        result = await repo.get_by_name("NoExiste")
        assert result is None

    async def test_get_all(self, db_session: AsyncSession) -> None:
        repo = RegionRepository(db_session)
        await repo.create(Region(name="CiudadA", lat=10.0, lon=20.0))
        await repo.create(Region(name="CiudadB", lat=11.0, lon=21.0))

        all_regions = await repo.get_all()
        names = {r.name for r in all_regions}
        assert "CiudadA" in names
        assert "CiudadB" in names
