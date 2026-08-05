"""
scripts/mock_rss_server.py — Mock RSS News Feed Server.

Returns RSS/XML feeds with realistic flood-related news articles.
Three feeds simulating NDTV, TOI, and NDMA press releases.

Run with:
    python backend/scripts/mock_rss_server.py
    # → http://localhost:8083

Endpoints:
  GET /feeds/ndtv     → NDTV Flood News
  GET /feeds/toi      → Times of India Disaster Desk
  GET /feeds/ndma     → NDMA Press Releases
  GET /feeds/all      → Combined JSON list (for testing)
"""
import uvicorn
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

app = FastAPI(title="RSS Mock Server", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_NOW = datetime.now(timezone.utc)

ARTICLES = [
    {
        "title": "Brahmaputra crosses danger mark in Guwahati; thousands evacuated in Kamrup",
        "url": "https://mock.ndtv.com/news/brahmaputra-danger-guwahati-001",
        "published": _NOW - timedelta(hours=2),
        "source": "NDTV Flood News",
        "district": "Kamrup Metropolitan",
        "state": "Assam",
        "summary": (
            "The Brahmaputra river has crossed the danger level at Guwahati, "
            "prompting authorities to issue flood warnings for downstream districts. "
            "NDRF teams have been deployed and over 4,000 residents evacuated from "
            "low-lying areas. Heavy rainfall forecast to continue for the next 48 hours."
        ),
    },
    {
        "title": "Godavari floods: 12 villages marooned in West Godavari district, relief camps set up",
        "url": "https://mock.ndtv.com/news/godavari-floods-polavaram-002",
        "published": _NOW - timedelta(hours=5),
        "source": "NDTV Flood News",
        "district": "West Godavari",
        "state": "Andhra Pradesh",
        "summary": (
            "Severe flooding along the Godavari river has cut off 12 villages in the "
            "West Godavari district. Water levels at Polavaram have breached the danger "
            "mark. The district administration has opened 8 relief camps. SDRF teams "
            "conducting rescue operations using boats."
        ),
    },
    {
        "title": "IMD issues Red alert for Assam: Extremely heavy rainfall expected over next 5 days",
        "url": "https://mock.toi.com/news/imd-red-alert-assam-003",
        "published": _NOW - timedelta(hours=8),
        "source": "Times of India Disaster Desk",
        "district": "Kamrup",
        "state": "Assam",
        "summary": (
            "The India Meteorological Department has issued a Red alert for Assam "
            "predicting extremely heavy rainfall. Flash floods and landslides are "
            "expected. Chief Minister has convened an emergency meeting with disaster "
            "management officials. NDRF has pre-positioned 10 teams."
        ),
    },
    {
        "title": "Hyderabad on flood watch as Musi overflows; GHMC issues advisory",
        "url": "https://mock.toi.com/news/hyderabad-musi-flood-watch-004",
        "published": _NOW - timedelta(hours=12),
        "source": "Times of India Disaster Desk",
        "district": "Hyderabad",
        "state": "Telangana",
        "summary": (
            "Heavy overnight rainfall has caused the Musi river to overflow its banks "
            "in low-lying areas of Hyderabad. GHMC has issued a flood advisory urging "
            "residents near Nagol and Nadeem Colony to evacuate. Rainfall of 85mm "
            "recorded in the last 24 hours."
        ),
    },
    {
        "title": "NDMA activates Emergency Operations Centre; flood relief funds released for 6 states",
        "url": "https://mock.ndma.gov.in/press/eoc-activation-005",
        "published": _NOW - timedelta(hours=3),
        "source": "NDMA Press Release",
        "district": None,
        "state": "National",
        "summary": (
            "The National Disaster Management Authority has activated its Emergency "
            "Operations Centre in response to severe flooding across Assam, Bihar, "
            "Andhra Pradesh, Telangana, Kerala, and Odisha. Central flood relief funds "
            "of Rs. 450 crore have been released. 15 NDRF battalions deployed."
        ),
    },
    {
        "title": "Kosi river floods: 30 villages affected in Bihar's Supaul district",
        "url": "https://mock.ndtv.com/news/kosi-floods-supaul-006",
        "published": _NOW - timedelta(hours=18),
        "source": "NDTV Flood News",
        "district": "Supaul",
        "state": "Bihar",
        "summary": (
            "Incessant rainfall in Nepal has swelled the Kosi river, inundating 30 "
            "villages in Supaul district. Over 15,000 people have been displaced. "
            "Floodwaters have damaged crops, roads, and embankments."
        ),
    },
]


def _rss_item(article: dict) -> str:
    pub = format_datetime(article["published"])
    return f"""
    <item>
      <title><![CDATA[{article['title']}]]></title>
      <link>{article['url']}</link>
      <pubDate>{pub}</pubDate>
      <description><![CDATA[{article['summary']}]]></description>
      <category>Flood</category>
    </item>"""


def _feed_xml(title: str, link: str, articles: list) -> str:
    items = "\n".join(_rss_item(a) for a in articles)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{title}</title>
    <link>{link}</link>
    <description>Flood and disaster news feed</description>
    <language>en-IN</language>
    <lastBuildDate>{format_datetime(_NOW)}</lastBuildDate>
    {items}
  </channel>
</rss>"""


XML_HEADER = {"Content-Type": "application/rss+xml; charset=utf-8"}


@app.get("/")
def root():
    return {"service": "RSS Mock Server", "feeds": ["/feeds/ndtv", "/feeds/toi", "/feeds/ndma"]}


@app.get("/feeds/ndtv")
def ndtv_feed():
    articles = [a for a in ARTICLES if "NDTV" in a["source"]]
    xml = _feed_xml("NDTV Flood News", "https://mock.ndtv.com/feeds/ndtv", articles)
    return Response(content=xml, media_type="application/rss+xml")


@app.get("/feeds/toi")
def toi_feed():
    articles = [a for a in ARTICLES if "Times" in a["source"]]
    xml = _feed_xml("TOI Disaster Desk", "https://mock.toi.com/feeds/toi", articles)
    return Response(content=xml, media_type="application/rss+xml")


@app.get("/feeds/ndma")
def ndma_feed():
    articles = [a for a in ARTICLES if "NDMA" in a["source"]]
    xml = _feed_xml("NDMA Press Releases", "https://mock.ndma.gov.in/feeds/ndma", articles)
    return Response(content=xml, media_type="application/rss+xml")


@app.get("/feeds/all")
def all_articles():
    return {"count": len(ARTICLES), "articles": ARTICLES}


if __name__ == "__main__":
    print("Starting RSS Mock Server on http://localhost:8083 …")
    uvicorn.run("mock_rss_server:app", host="0.0.0.0", port=8083, reload=True)
