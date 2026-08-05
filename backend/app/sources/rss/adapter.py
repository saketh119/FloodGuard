"""
sources/rss/adapter.py — RSS / News Feed Adapter.

Polls three RSS feeds, runs keyword matching, and returns
NewsObservation objects for flood-relevant articles.

Keywords are checked in title + summary. An article is "triggered"
if it contains >= 2 unique keyword stems.
"""
import json
from datetime import datetime, timezone
from typing import Optional

import feedparser

from app.core.logger import get_logger
from app.models.news import NewsObservation

log = get_logger(__name__)

# RSS feed URLs (pointing at mock server; update for production)
RSS_FEEDS = [
    "http://localhost:8083/feeds/ndtv",
    "http://localhost:8083/feeds/toi",
    "http://localhost:8083/feeds/ndma",
]

# Keyword list (case-insensitive, stem-matched)
FLOOD_KEYWORDS = [
    "flood", "flooding", "inundation", "waterlogging",
    "deluge", "submerge", "overflow", "overflowed",
    "danger level", "warning level", "breach", "embankment",
    "evacuate", "evacuation", "ndrf", "sdrf", "rescue",
    "cyclone", "cloudburst", "landslide", "heavy rain",
    "red alert", "orange alert", "disaster", "relief camp",
]

# District name → state lookup for location extraction
DISTRICT_STATE_MAP = {
    "kamrup": "Assam", "guwahati": "Assam", "assam": "Assam",
    "west godavari": "Andhra Pradesh", "ntr": "Andhra Pradesh",
    "andhra": "Andhra Pradesh", "polavaram": "Andhra Pradesh",
    "hyderabad": "Telangana", "telangana": "Telangana",
    "patna": "Bihar", "supaul": "Bihar", "bihar": "Bihar",
    "ernakulam": "Kerala", "kerala": "Kerala",
}


class RSSAdapter:

    async def ingest_all(self) -> list[NewsObservation]:
        """Poll all RSS feeds and return flood-relevant NewsObservation objects."""
        results = []
        for feed_url in RSS_FEEDS:
            articles = self._poll_feed(feed_url)
            results.extend(articles)
        log.info(f"RSS: found {len(results)} triggered articles across {len(RSS_FEEDS)} feeds")
        return results

    def _poll_feed(self, feed_url: str) -> list[NewsObservation]:
        try:
            parsed = feedparser.parse(feed_url)
        except Exception as exc:
            log.warning(f"RSS parse failed for {feed_url}: {exc}")
            return []

        observations = []
        for entry in parsed.entries:
            title   = entry.get("title", "")
            summary = entry.get("summary", entry.get("description", ""))
            url     = entry.get("link")
            pub     = self._parse_date(entry)

            full_text = f"{title} {summary}".lower()
            matched = [kw for kw in FLOOD_KEYWORDS if kw in full_text]

            if len(matched) < 2:
                continue  # Not flood-relevant

            district, state = self._extract_location(full_text)

            observations.append(NewsObservation(
                title=title[:500],
                url=url,
                published_at=pub,
                source_feed=feed_url,
                content_snippet=summary[:2000] if summary else None,
                district=district,
                state=state,
                flood_keywords=",".join(matched[:20]),
                keyword_count=len(matched),
                triggered=True,
                raw_json=json.dumps({
                    "title": title,
                    "url": url,
                    "summary": summary[:500],
                }),
            ))

        return observations

    def _parse_date(self, entry) -> Optional[datetime]:
        try:
            import time as _time
            t = entry.get("published_parsed") or entry.get("updated_parsed")
            if t:
                return datetime.fromtimestamp(_time.mktime(t), tz=timezone.utc)
        except Exception:
            pass
        return datetime.now(timezone.utc)

    def _extract_location(self, text: str) -> tuple[Optional[str], Optional[str]]:
        for district_key, state in DISTRICT_STATE_MAP.items():
            if district_key in text:
                # Capitalize properly
                district = district_key.title()
                return district, state
        return None, None
