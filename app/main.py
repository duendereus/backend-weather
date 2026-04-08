import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import (
    IncentiveConfigNotFoundError,
    RegionNotFoundError,
    WeatherServiceUnavailableError,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting Fleet Investment Service [%s]", settings.ENVIRONMENT)
    yield
    logger.info("Shutting down Fleet Investment Service")


app = FastAPI(
    title="Fleet Investment Service",
    description="Microservicio de Rappi para calcular inversión en flota según clima",
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(WeatherServiceUnavailableError)
async def weather_unavailable_handler(
    request: Request, exc: WeatherServiceUnavailableError
) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(RegionNotFoundError)
async def region_not_found_handler(
    request: Request, exc: RegionNotFoundError
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(IncentiveConfigNotFoundError)
async def incentive_config_not_found_handler(
    request: Request, exc: IncentiveConfigNotFoundError
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
