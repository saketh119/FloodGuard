"""
models/__init__.py — Import all ORM models so SQLAlchemy's metadata
knows about every table when create_all_tables() is called.
"""
from app.models import imd, cwc, weather, news, events, predictions  # noqa: F401
