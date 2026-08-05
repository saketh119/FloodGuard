"""
pipeline/trigger.py — Trigger Detection.

Each observation type has its own rule set. The TriggerDetector
inspects a normalized observation object and returns either a
TriggerResult (event should be created/updated) or None (ignore).

Rules:
  IMD:     nowcast_color >= 3 (Orange/Red) OR rain_24h > 64.5mm
  CWC:     status in ('warning', 'danger', 'severe')
  Weather: rainfall_1h > 15mm OR wind_speed > 50 km/h
  News:    keyword_count >= 2 (already filtered by RSS adapter)
"""
from dataclasses import dataclass
from typing import Optional

from app.models.cwc import CwcMeasurement
from app.models.imd import ImdObservation
from app.models.news import NewsObservation
from app.models.weather import WeatherObservation


@dataclass
class TriggerResult:
    source: str          # imd | cwc | weather | news
    observation_id: int
    observation_table: str
    district: Optional[str]
    state: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    reason: str
    contribution_score: float  # 0.0 – 1.0, how strongly this observation triggers
    raw_obs: object            # reference to the ORM object


class TriggerDetector:
    """
    Stateless trigger evaluator. Call check() with any observation object.
    """

    def check(self, obs) -> Optional[TriggerResult]:
        if isinstance(obs, ImdObservation):
            return self._check_imd(obs)
        if isinstance(obs, CwcMeasurement):
            return self._check_cwc(obs)
        if isinstance(obs, WeatherObservation):
            return self._check_weather(obs)
        if isinstance(obs, NewsObservation):
            return self._check_news(obs)
        return None

    # ── IMD rules ──────────────────────────────────────────────────────
    def _check_imd(self, obs: ImdObservation) -> Optional[TriggerResult]:
        reasons = []
        score = 0.0

        color = obs.nowcast_color or 1
        rain  = obs.rain_24h or 0.0

        if color == 4:          # Red
            reasons.append(f"Red nowcast alert")
            score = max(score, 0.75)
        elif color == 3:        # Orange
            reasons.append(f"Orange nowcast alert")
            score = max(score, 0.50)

        if rain > 115.5:        # Extremely heavy (IMD threshold)
            reasons.append(f"Extremely heavy rain: {rain:.1f}mm")
            score = max(score, 0.80)
        elif rain > 64.5:       # Heavy rain
            reasons.append(f"Heavy rain: {rain:.1f}mm")
            score = max(score, 0.45)

        if not reasons:
            return None

        return TriggerResult(
            source="imd",
            observation_id=obs.id,
            observation_table="imd_observation",
            district=obs.district_name,
            state=obs.state,
            lat=obs.lat,
            lng=obs.lng,
            reason="; ".join(reasons),
            contribution_score=min(score, 1.0),
            raw_obs=obs,
        )

    # ── CWC rules ──────────────────────────────────────────────────────
    def _check_cwc(self, obs: CwcMeasurement) -> Optional[TriggerResult]:
        STATUS_SCORE = {"warning": 0.50, "danger": 0.75, "severe": 0.90}
        score = STATUS_SCORE.get(obs.status)
        if not score:
            return None

        station = obs.station  # ORM relationship
        return TriggerResult(
            source="cwc",
            observation_id=obs.id,
            observation_table="cwc_measurement",
            district=station.district if station else None,
            state=station.state if station else None,
            lat=station.lat if station else None,
            lng=station.lng if station else None,
            reason=f"River level {obs.status}: {obs.water_level:.2f}m",
            contribution_score=score,
            raw_obs=obs,
        )

    # ── Weather rules ──────────────────────────────────────────────────
    def _check_weather(self, obs: WeatherObservation) -> Optional[TriggerResult]:
        reasons = []
        score = 0.0

        if (obs.rainfall_1h or 0) > 35.0:
            reasons.append(f"Very heavy rain: {obs.rainfall_1h:.1f}mm/h")
            score = max(score, 0.55)
        elif (obs.rainfall_1h or 0) > 15.0:
            reasons.append(f"Heavy rain: {obs.rainfall_1h:.1f}mm/h")
            score = max(score, 0.35)

        if (obs.wind_speed or 0) > 80.0:
            reasons.append(f"Cyclonic wind: {obs.wind_speed:.0f}km/h")
            score = max(score, 0.65)
        elif (obs.wind_speed or 0) > 50.0:
            reasons.append(f"Strong wind: {obs.wind_speed:.0f}km/h")
            score = max(score, 0.30)

        if not reasons:
            return None

        return TriggerResult(
            source="weather",
            observation_id=obs.id,
            observation_table="weather_observation",
            district=obs.district,
            state=obs.state,
            lat=obs.lat,
            lng=obs.lng,
            reason="; ".join(reasons),
            contribution_score=min(score, 1.0),
            raw_obs=obs,
        )

    # ── News rules ─────────────────────────────────────────────────────
    def _check_news(self, obs: NewsObservation) -> Optional[TriggerResult]:
        if (obs.keyword_count or 0) < 2:
            return None

        # Score proportional to keyword density (capped at 0.40 — news is soft evidence)
        score = min(0.10 + (obs.keyword_count * 0.03), 0.40)

        return TriggerResult(
            source="news",
            observation_id=obs.id,
            observation_table="news_observation",
            district=obs.district,
            state=obs.state,
            lat=None,
            lng=None,
            reason=f"Flood news: {obs.keyword_count} keywords ({obs.flood_keywords[:80]})",
            contribution_score=score,
            raw_obs=obs,
        )
