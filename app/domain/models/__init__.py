from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Register all models so Alembic can detect them
from app.domain.models.incentive_config import IncentiveConfig as IncentiveConfig
from app.domain.models.investment_evaluation import InvestmentEvaluation as InvestmentEvaluation
from app.domain.models.region import Region as Region
from app.domain.models.weather_snapshot import WeatherSnapshot as WeatherSnapshot
