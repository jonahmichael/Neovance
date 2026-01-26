"""
Database configuration and connection management for PostgreSQL/TimescaleDB
"""

import os
import asyncpg
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# Database Configuration
class DatabaseConfig:
    # PostgreSQL connection parameters
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "neovance_db")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    
    # Connection URLs
    ASYNC_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SYNC_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Connection pool settings
    POOL_SIZE = 20
    MAX_OVERFLOW = 30
    POOL_TIMEOUT = 30
    POOL_RECYCLE = 3600

# SQLAlchemy Base
class Base(DeclarativeBase):
    pass

# Global engine and session factory
engine = create_async_engine(
    DatabaseConfig.ASYNC_DATABASE_URL,
    pool_size=DatabaseConfig.POOL_SIZE,
    max_overflow=DatabaseConfig.MAX_OVERFLOW,
    pool_timeout=DatabaseConfig.POOL_TIMEOUT,
    pool_recycle=DatabaseConfig.POOL_RECYCLE,
    echo=False,  # Set to True for SQL query logging
)

# Session factory
async_session_factory = async_sessionmaker(
    engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency for FastAPI
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to provide database session"""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

# Context manager for standalone database operations
@asynccontextmanager
async def get_db():
    """Context manager for database operations outside FastAPI"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

# Direct connection for Pathway ETL
def get_pathway_db_url():
    """Get sync database URL for Pathway ETL"""
    return DatabaseConfig.SYNC_DATABASE_URL

# Database initialization
async def init_database():
    """Initialize database tables"""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
        # Enable TimescaleDB extension (if not already enabled)
        try:
            await conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
        except Exception as e:
            print(f"TimescaleDB extension setup: {e}")

# Database health check
async def check_database_health():
    """Check if database is accessible and TimescaleDB is enabled"""
    try:
        async with async_session_factory() as session:
            # Test basic connectivity
            result = await session.execute(sa.text("SELECT 1"))
            
            # Check TimescaleDB
            result = await session.execute(
                sa.text("SELECT * FROM pg_extension WHERE extname = 'timescaledb'")
            )
            timescale_enabled = result.first() is not None
            
            return {
                "database_connected": True,
                "timescaledb_enabled": timescale_enabled,
                "connection_url": DatabaseConfig.ASYNC_DATABASE_URL.replace(DatabaseConfig.DB_PASSWORD, "***")
            }
    except Exception as e:
        return {
            "database_connected": False,
            "error": str(e),
            "connection_url": DatabaseConfig.ASYNC_DATABASE_URL.replace(DatabaseConfig.DB_PASSWORD, "***")
        }

# Utility function for raw SQL execution (useful for HIL analytics)
async def execute_raw_sql(query: str, params: dict = None):
    """Execute raw SQL query with optional parameters"""
    async with async_session_factory() as session:
        result = await session.execute(sa.text(query), params or {})
        await session.commit()
        return result

# Legacy SQLite fallback (for gradual migration)
def create_sqlite_fallback():
    """Create SQLite engine as fallback during migration"""
    return sa.create_engine("sqlite:///neonatal_ehr.db", echo=False)