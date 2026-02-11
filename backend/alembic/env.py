"""Alembic environment configuration with async support."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from talent_inbound.config import get_settings
from talent_inbound.shared.infrastructure.database import Base

# Import all ORM models so Alembic can detect them for autogenerate.
# Add new model imports here as modules are implemented.
from talent_inbound.modules.auth.infrastructure.orm_models import *  # noqa: F401,F403
# from talent_inbound.modules.profile.infrastructure.orm_models import *  # noqa
# from talent_inbound.modules.ingestion.infrastructure.orm_models import *  # noqa
# from talent_inbound.modules.opportunities.infrastructure.orm_models import *  # noqa
# from talent_inbound.modules.chat.infrastructure.orm_models import *  # noqa

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

settings = get_settings()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL without DB connection)."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connects to DB asynchronously)."""
    connectable = create_async_engine(settings.database_url)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
