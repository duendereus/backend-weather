"""Dependency providers for FastAPI's Depends() system."""

from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import async_session_factory
from app.infrastructure.weather_client.base import WeatherClient
from app.infrastructure.weather_client.owm_client import OWMClient
from app.repositories.config_repository import ConfigRepository
from app.repositories.investment_repository import InvestmentRepository
from app.repositories.region_repository import RegionRepository
from app.repositories.weather_repository import WeatherRepository
from app.services.investment_service import InvestmentService
from app.services.weather_service import WeatherService


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session, session.begin():
        yield session


def get_weather_client() -> WeatherClient:
    return OWMClient()


def get_config_repo(session: AsyncSession = Depends(get_session)) -> ConfigRepository:
    return ConfigRepository(session)


def get_investment_repo(session: AsyncSession = Depends(get_session)) -> InvestmentRepository:
    return InvestmentRepository(session)


def get_region_repo(session: AsyncSession = Depends(get_session)) -> RegionRepository:
    return RegionRepository(session)


def get_weather_repo(session: AsyncSession = Depends(get_session)) -> WeatherRepository:
    return WeatherRepository(session)


def get_weather_service(
    weather_client: WeatherClient = Depends(get_weather_client),
    weather_repo: WeatherRepository = Depends(get_weather_repo),
    region_repo: RegionRepository = Depends(get_region_repo),
) -> WeatherService:
    return WeatherService(
        weather_client=weather_client,
        weather_repo=weather_repo,
        region_repo=region_repo,
    )


def get_investment_service(
    config_repo: ConfigRepository = Depends(get_config_repo),
    investment_repo: InvestmentRepository = Depends(get_investment_repo),
) -> InvestmentService:
    return InvestmentService(
        config_repo=config_repo,
        investment_repo=investment_repo,
    )
