"""Dependency providers for FastAPI's Depends() system."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import async_session_factory
from app.infrastructure.weather_client.base import WeatherClient
from app.infrastructure.weather_client.owm_client import OWMClient


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session


def get_weather_client() -> WeatherClient:
    return OWMClient()
