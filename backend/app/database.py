"""
Database Engine & Session Management for SQLite using SQLAlchemy and aiosqlite.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from backend.app.config import DATABASE_URL, SYNC_DATABASE_URL

# Async Engine for FastAPI routes
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Synchronous Engine for background jobs / model callbacks
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    """FastAPI dependency for async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_sync_db():
    """Helper for background threads and sync workers."""
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()

async def init_db():
    """Initializes all tables synchronously via sync engine to avoid SQLite thread lock contention."""
    import backend.app.models  # ensure models are registered
    Base.metadata.create_all(bind=sync_engine)
