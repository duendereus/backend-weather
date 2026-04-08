import ssl
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def _build_connect_args() -> dict[str, object]:
    """Return extra connect_args for asyncpg. Neon requires SSL."""
    if not settings.DATABASE_SSL:
        return {}
    ssl_ctx = ssl.create_default_context()
    return {"ssl": ssl_ctx}


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=_build_connect_args(),
    pool_pre_ping=True,        # test connection before using it (handles Neon idle disconnects)
    pool_recycle=300,           # recycle connections every 5 min
    pool_size=5,
    max_overflow=10,
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session
