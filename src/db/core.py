import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.config import SQLALCHEMY_DATABASE_URL

logger = logging.getLogger(__name__)

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    pass


@asynccontextmanager
async def GetDB() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            yield session


async def create_migration_engine():
    return create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        poolclass=None,
    )
