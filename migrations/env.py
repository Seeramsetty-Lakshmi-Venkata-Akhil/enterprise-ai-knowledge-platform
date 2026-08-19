import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

import enterprise_ai.persistence.models  # noqa: F401
from enterprise_ai.core.config import get_settings
from enterprise_ai.persistence.base import Base

# Alembic's main configuration object.
# It reads values from alembic.ini.
config = context.config


# Load our application settings so Alembic uses the same database
# configuration as the FastAPI application.
settings = get_settings()

# Override the placeholder sqlalchemy.url from alembic.ini
# with the real DATABASE_URL from our application settings.
config.set_main_option("sqlalchemy.url", settings.database_url)


# Configure Alembic's own logging using alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Alembic uses this metadata to discover SQLAlchemy models.
# Every future model that inherits from Base contributes to Base.metadata.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations without creating a live database connection.

    In offline mode, Alembic generates SQL statements instead of
    directly executing them against PostgreSQL.
    """

    # Read the database URL that we set above.
    url = config.get_main_option("sqlalchemy.url")

    # Configure Alembic using only the database URL and model metadata.
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    # Start a migration transaction context and generate migration SQL.
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# Alembic decides which mode to use depending on the command being executed.
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
