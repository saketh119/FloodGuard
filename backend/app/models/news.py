"""
models/news.py — RSS / News observation table.

Stores flood-related news articles extracted from RSS feeds.
Keyword matching determines flood relevance at ingestion time.
"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NewsObservation(Base):
    __tablename__ = "news_observation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True, unique=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, index=True, nullable=True)
    source_feed: Mapped[str | None] = mapped_column(String(200), nullable=True)

    content_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Extracted location clues from article text
    district: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    state: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)

    # Comma-separated flood keywords found in article
    flood_keywords: Mapped[str | None] = mapped_column(String(500), nullable=True)
    keyword_count: Mapped[int] = mapped_column(Integer, default=0)

    # Trigger flag (True if keyword_count >= threshold)
    triggered: Mapped[bool] = mapped_column(Integer, default=0)

    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<NewsObs id={self.id} '{self.title[:60]}…'>"
