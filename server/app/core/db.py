from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from pgvector.asyncpg import register_vector
from sqlalchemy import event
from sqlalchemy.engine import AdaptedConnection
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.settings import get_settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    get_settings().database_url,
    pool_pre_ping=True,
)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


@event.listens_for(engine.sync_engine, "connect")
def register_pgvector(
    dbapi_connection: AdaptedConnection,
    _connection_record: object,
) -> None:
    dbapi_connection.run_async(register_vector)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


SessionDep = Annotated[AsyncSession, Depends(get_session)]
