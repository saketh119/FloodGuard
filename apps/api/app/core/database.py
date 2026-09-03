"""SQLite engine + session factory.

SQLite keeps the 2-hour slice dependency-free; the SADD calls for PostgreSQL and
every model here is plain SQLAlchemy 2.0, so the move is a DATABASE_URL change.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.DATABASE_URL,
    # check_same_thread=False: the APScheduler job runs off the request thread.
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def get_db():
    """FastAPI dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401  (registers mappers)
    Base.metadata.create_all(bind=engine)
