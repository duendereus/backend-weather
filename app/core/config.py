from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Required
    OWM_API_KEY: str
    DATABASE_URL: str = "postgresql+asyncpg://rappi:rappi@db:5432/fleet_invest"

    # OpenWeatherMap
    OWM_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    OWM_TIMEOUT_SECONDS: int = 10

    # Scheduler
    SNAPSHOT_INTERVAL_MINUTES: int = 15

    # App
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Railway/Neon — Neon requires SSL; Railway provides PORT
    DATABASE_SSL: bool = False
    PORT: int = 8000


settings = Settings()
