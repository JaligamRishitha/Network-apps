"""
Database connection and session management with async support.
Requirements: 9.2 - SQLAlchemy ORM with PostgreSQL
"""
import os
from typing import AsyncGenerator, Optional
from sqlalchemy.orm import declarative_base

# Base class for all models - always available
Base = declarative_base()

# Lazy initialization of engine and session factory
_engine = None
_async_session_local = None


def _get_engine():
    """Lazily create the async engine."""
    global _engine
    if _engine is None:
        from sqlalchemy.ext.asyncio import create_async_engine
        from backend.config import get_settings
        
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def _get_session_factory():
    """Lazily create the session factory."""
    global _async_session_local
    if _async_session_local is None:
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
        
        _async_session_local = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_local


# Properties for backward compatibility
@property
def engine():
    return _get_engine()


@property  
def AsyncSessionLocal():
    return _get_session_factory()


async def get_db() -> AsyncGenerator:
    """
    Dependency injection for database sessions.
    Yields an async session and ensures proper cleanup.
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    
    session_factory = _get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
