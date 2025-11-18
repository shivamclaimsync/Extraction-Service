"""Async database session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
import logging

logger = logging.getLogger(__name__)


class DatabaseSession:
    """Manages async PostgreSQL database sessions using asyncpg."""
    
    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
    ):
        """
        Initialize database session manager.
        
        Args:
            database_url: PostgreSQL connection URL with asyncpg driver
                         (e.g., 'postgresql+asyncpg://user:pass@localhost/db')
            echo: Whether to log all SQL statements
            pool_size: Number of connections to maintain in the pool
            max_overflow: Maximum number of connections to create beyond pool_size
        """
        self.database_url = database_url
        
        # Create async engine
        self.engine: AsyncEngine = create_async_engine(
            database_url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
            connect_args={
                "server_settings": {
                    "application_name": "extraction_service",
                },
                "command_timeout": 60,  # 60 second timeout for commands
            },
        )
        
        # Create session factory
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
        )
        
        logger.info("Database session manager initialized")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session (context manager).
        
        Usage:
            async with db_session.get_session() as session:
                result = await session.execute(query)
        
        Yields:
            AsyncSession instance
        """
        async with self.async_session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """Close the database engine and all connections."""
        await self.engine.dispose()
        logger.info("Database connections closed")


# Global database session instance
_db_session: Optional[DatabaseSession] = None


def init_db(
    database_url: str,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
) -> DatabaseSession:
    """
    Initialize the global database session.
    
    Args:
        database_url: PostgreSQL connection URL with asyncpg driver
        echo: Whether to log SQL statements
        pool_size: Connection pool size
        max_overflow: Maximum overflow connections
        
    Returns:
        DatabaseSession instance
    """
    global _db_session
    _db_session = DatabaseSession(
        database_url=database_url,
        echo=echo,
        pool_size=pool_size,
        max_overflow=max_overflow,
    )
    return _db_session


def get_db() -> DatabaseSession:
    """
    Get the global database session.
    
    Returns:
        DatabaseSession instance
        
    Raises:
        RuntimeError: If database not initialized
    """
    if _db_session is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() first."
        )
    return _db_session

