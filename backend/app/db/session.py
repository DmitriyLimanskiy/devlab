from collections.abc import AsyncGenerator
from functools import lru_cache

from app.database import database_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Создать один engine на процесс; соединение откроется при первом запросе"""
    return create_async_engine(database_url(), pool_pre_ping=True)


@lru_cache(maxsize=1)
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Получить общую фабрику, создающую отдельную сессию для каждой операции"""
    return async_sessionmaker(bind=get_engine(), expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Выдать сессию через Depends и закрыть после обработки запроса"""
    async with get_session_factory()() as session:
        yield session
