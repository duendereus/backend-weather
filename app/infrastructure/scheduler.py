"""APScheduler setup for periodic weather snapshot jobs."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.infrastructure.database import async_session_factory
from app.infrastructure.weather_client.owm_client import OWMClient
from app.repositories.config_repository import ConfigRepository
from app.repositories.investment_repository import InvestmentRepository
from app.repositories.region_repository import RegionRepository
from app.repositories.weather_repository import WeatherRepository
from app.services.snapshot_service import SnapshotService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _run_snapshot_job() -> None:
    """Execute a single snapshot run with its own DB session."""
    logger.info("Snapshot job triggered")
    async with async_session_factory() as session:
        async with session.begin():
            service = SnapshotService(
                weather_client=OWMClient(),
                weather_repo=WeatherRepository(session),
                region_repo=RegionRepository(session),
                config_repo=ConfigRepository(session),
                investment_repo=InvestmentRepository(session),
            )
            await service.run()
    logger.info("Snapshot job completed")


def start_scheduler() -> None:
    """Register the snapshot job and start the scheduler."""
    scheduler.add_job(
        _run_snapshot_job,
        trigger=IntervalTrigger(minutes=settings.SNAPSHOT_INTERVAL_MINUTES),
        id="snapshot_job",
        name="Periodic weather snapshot",
        replace_existing=True,
    )
    if not scheduler.running:
        scheduler.start()
    logger.info(
        "Scheduler started — snapshot job every %d minutes",
        settings.SNAPSHOT_INTERVAL_MINUTES,
    )


def stop_scheduler() -> None:
    """Shut down the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
