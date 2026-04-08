"""Fixtures for integration tests — require a running PostgreSQL instance."""

import asyncio
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_session, get_weather_client
from app.core.config import settings
from app.domain.models import Base
from app.main import app


@pytest.fixture(scope="session")
def event_loop():  # type: ignore[no-untyped-def]
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine():  # type: ignore[no-untyped-def]
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncIterator[AsyncSession]:  # type: ignore[no-untyped-def]
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:  # type: ignore[no-untyped-def]
    """AsyncClient wired to the FastAPI app with overridden DB session."""
    from tests.fakes import FakeWeatherClient

    async def _override_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_weather_client] = FakeWeatherClient

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
