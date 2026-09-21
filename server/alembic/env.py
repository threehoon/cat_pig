import asyncio
import pkgutil
from importlib import import_module, util
from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app import modules
from app.core.db import Base
from app.core.settings import get_settings


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def import_module_models() -> None:
    prefix = f"{modules.__name__}."
    for module_info in pkgutil.iter_modules(modules.__path__, prefix):
        if not module_info.ispkg:
            continue
        models_name = f"{module_info.name}.models"
        if util.find_spec(models_name) is not None:
            import_module(models_name)


import_module_models()
target_metadata = Base.metadata


def get_database_url() -> str:
    return get_settings().database_url


def run_migrations_offline() -> None:
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_database_url()
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
