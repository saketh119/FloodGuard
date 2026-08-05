"""
core/database.py — Async SQLAlchemy engine and session factory.

Usage:
    async with get_db() as db:
        result = await db.execute(select(FloodEvent))
"""
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# ── Engine ────────────────────────────────────────────────────────────
# connect_args only needed for SQLite to allow multi-thread access
_connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args=_connect_args,
)

# ── Session factory ───────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Base for all ORM models ───────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Dependency / context manager ──────────────────────────────────────
@asynccontextmanager
async def get_db():
    """Async context manager that yields a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_all_tables() -> None:
    """Create all tables (used on startup in dev)."""
    async with engine.begin() as conn:
        from app.models import imd, cwc, weather, news, events, predictions  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
