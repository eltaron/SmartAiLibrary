"""
shared/db.py
Async SQLAlchemy engine and session factory for PostgreSQL.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool

from shared.config import settings


class DatabaseManager:
    """Manages async database connections with connection pooling."""

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: sessionmaker | None = None

    def init(self) -> None:
        """Initialize the database engine and session factory."""
        self._engine = create_async_engine(
            settings.DATABASE_URL,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            echo=False,
            future=True,
        )
        self._session_factory = sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        """Get the database engine."""
        if self._engine is None:
            self.init()
        return self._engine

    @property
    def session_factory(self) -> sessionmaker:
        """Get the session factory."""
        if self._session_factory is None:
            self.init()
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Create a new database session."""
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def close(self) -> None:
        """Close the database engine."""
        if self._engine is not None:
            await self._engine.dispose()


db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting database sessions.
    Yields a session and handles commit/rollback automatically.
    """
    async with db_manager.session() as session:
        yield session