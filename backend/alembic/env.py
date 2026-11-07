from alembic import context
import asyncio
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.config import database_url
from app.db.base import Base
from app.db import models  # Регистрация всех таблиц в metadata для autogenerate


def offline():
    """Настроить генерацию SQL миграций без подключения к БД"""
    # Offline SQL не требует ни подключения, ни настоящих секретов
    context.configure(
        url="postgresql+psycopg://",
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations(connection):
    """Выполнить миграции в контексте переданного подключения"""
    context.configure(
        connection=connection, target_metadata=Base.metadata, compare_type=True
    )
    with context.begin_transaction():
        context.run_migrations()


async def online():
    """Выполнить миграции через асинхронное подключение к PostgreSQL"""
    engine = create_async_engine(database_url(), poolclass=pool.NullPool)
    try:
        async with engine.connect() as connection:
            await connection.run_sync(run_migrations)
    finally:
        await engine.dispose()


if context.is_offline_mode():
    offline()
elif context.config.attributes.get("connection") is not None:
    run_migrations(context.config.attributes["connection"])
else:
    asyncio.run(online())
