"""Database connection management for PostgreSQL.

This module provides SQLAlchemy engine and session management
with support for multi-tenant architecture and connection pooling.
"""

import logging
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import database_config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection and session manager.

    Provides both sync and async database connections with proper
    connection pooling and multi-tenant support.
    """

    def __init__(self) -> None:
        """Initialize database manager with connection pools."""
        self._sync_engine = None
        self._async_engine = None
        self._sync_session_factory = None
        self._async_session_factory = None
        self._initialize_engines()

    def _initialize_engines(self) -> None:
        """Initialize SQLAlchemy engines with connection pooling."""
        db_url = database_config.get_database_url()

        # Check if we're using SQLite (for testing)
        is_sqlite = db_url.startswith("sqlite")

        if is_sqlite:
            # SQLite configuration - no connection pooling needed
            self._sync_engine = create_engine(
                db_url,
                echo=database_config.echo_sql,
                future=True,
                connect_args={"check_same_thread": False},  # Needed for SQLite
            )

            self._async_engine = create_async_engine(
                database_config.get_async_database_url(),
                echo=database_config.echo_sql,
                future=True,
            )
        else:
            # PostgreSQL configuration with connection pooling
            self._sync_engine = create_engine(
                db_url,
                pool_size=database_config.pool_size,
                max_overflow=database_config.max_overflow,
                pool_timeout=database_config.pool_timeout,
                pool_recycle=database_config.pool_recycle,
                echo=database_config.echo_sql,
                future=True,
            )

            self._async_engine = create_async_engine(
                database_config.get_async_database_url(),
                pool_size=database_config.pool_size,
                max_overflow=database_config.max_overflow,
                pool_timeout=database_config.pool_timeout,
                pool_recycle=database_config.pool_recycle,
                echo=database_config.echo_sql,
                future=True,
            )

        # Session factories
        self._sync_session_factory = sessionmaker(
            bind=self._sync_engine,
            class_=Session,
            expire_on_commit=False,
        )

        self._async_session_factory = async_sessionmaker(
            bind=self._async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info(
            f"Initialized database connections to {database_config.get_database_url(include_password=False)}"
        )

    @property
    def sync_engine(self):
        """Get synchronous SQLAlchemy engine."""
        return self._sync_engine

    @property
    def async_engine(self):
        """Get asynchronous SQLAlchemy engine."""
        return self._async_engine

    @contextmanager
    def get_sync_session(self) -> Generator[Session, None, None]:
        """Get synchronous database session with automatic cleanup.

        Yields:
            SQLAlchemy session for synchronous operations

        Example:
            with db_manager.get_sync_session() as session:
                result = session.execute(text("SELECT 1"))
        """
        session = self._sync_session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get asynchronous database session with automatic cleanup.

        Yields:
            SQLAlchemy async session for asynchronous operations

        Example:
            async with db_manager.get_async_session() as session:
                result = await session.execute(text("SELECT 1"))
        """
        session = self._async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    def set_tenant_schema(self, session: Session, tenant_id: str) -> None:
        """Set the search path for multi-tenant isolation.

        Args:
            session: Database session
            tenant_id: Tenant identifier for schema isolation
        """
        if database_config.enable_multi_tenant:
            schema_name = f"tenant_{tenant_id}"
            session.execute(f"SET search_path TO {schema_name}, public")
            logger.debug(f"Set search path to {schema_name} for tenant {tenant_id}")

    async def set_tenant_schema_async(
        self, session: AsyncSession, tenant_id: str
    ) -> None:
        """Set the search path for multi-tenant isolation (async).

        Args:
            session: Async database session
            tenant_id: Tenant identifier for schema isolation
        """
        if database_config.enable_multi_tenant:
            schema_name = f"tenant_{tenant_id}"
            await session.execute(f"SET search_path TO {schema_name}, public")
            logger.debug(f"Set search path to {schema_name} for tenant {tenant_id}")

    def close_connections(self) -> None:
        """Close all database connections."""
        if self._sync_engine:
            self._sync_engine.dispose()
        if self._async_engine:
            # Use sync_dispose() for async engines to avoid RuntimeWarning
            self._async_engine.sync_engine.dispose()
        logger.info("Closed all database connections")


# Global database manager instance
db_manager = DatabaseManager()

# Test session override for integration tests
_test_session = None


def set_test_session(session: Session) -> None:
    """Set the test session for integration tests."""
    global _test_session
    _test_session = session


# Dependency injection functions for FastAPI
def get_sync_db() -> Generator[Session, None, None]:
    """FastAPI dependency for synchronous database sessions."""
    import os

    if os.environ.get("TESTING") == "true" and _test_session is not None:
        print(f"DEBUG: Returning test session: {_test_session}")
        yield _test_session
    else:
        print("DEBUG: Returning new session from db_manager")
        with db_manager.get_sync_session() as session:
            yield session


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for asynchronous database sessions."""
    async with db_manager.get_async_session() as session:
        yield session
