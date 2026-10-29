"""Миграции запускаются только явной командой Alembic."""
from alembic import context
from sqlalchemy import create_engine, pool

from app.database import database_url
from app.schemas import Base


def offline():
    # Offline SQL не требует ни подключения, ни настоящих секретов.
    context.configure(url='postgresql+psycopg://', target_metadata=Base.metadata,
                      literal_binds=True, dialect_opts={'paramstyle': 'named'}, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def online():
    engine = create_engine(database_url(), poolclass=pool.NullPool)
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    offline()
else:
    online()
