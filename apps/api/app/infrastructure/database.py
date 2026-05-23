from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings
from app.core.errors import ConfigurationError


class Base(DeclarativeBase):
    pass


@lru_cache
def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    settings = get_settings()
    if not settings.database_url:
        raise ConfigurationError("DATABASE_URL is required")
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    async_session_factory = get_async_session_factory()
    async with async_session_factory() as session:
        yield session
