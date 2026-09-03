"""Trigger detection — decides whether a single observation is worth reacting to.

Thresholds follow IMD's own published rainfall classification and 4-colour warning
scheme, so the numbers here are defensible rather than invented:
  Heavy rain           64.5 - 115.5 mm/day
  Very heavy rain     115.6 - 204.4 mm/day
  Extremely heavy     >= 204.5 mm/day
  Colour codes        1 Green (none) · 2 Yellow (watch) · 3 Orange (alert) · 4 Red (warning)
"""
from dataclasses import dataclass

from app.models import ImdObservation

HEAVY_MM = 64.5
VERY_HEAVY_MM = 115.6
EXTREMELY_HEAVY_MM = 204.5

COLOR_NAMES = {1: "Green", 2: "Yellow", 3: "Orange", 4: "Red"}
SEVERITY_ORDER = ["low", "moderate", "high", "severe"]


@dataclass
class Trigger:
    fired: bool
    severity: str = "low"
    reason: str = ""
    contribution: float = 0.0   # how much this evidence adds to event confidence
    category: str = "heavy_rainfall"

    @staticmethod
    def none() -> "Trigger":
        return Trigger(fired=False)


def _rainfall_severity(mm: float) -> str:
    if mm >= EXTREMELY_HEAVY_MM:
        return "severe"
    if mm >= VERY_HEAVY_MM:
        return "high"
    return "moderate"


def evaluate(obs: ImdObservation) -> Trigger:
    """Route an observation to its source-specific rule."""
    t = obs.observation_type

    if t in ("nowcast", "warning"):
        color = obs.color_code or 0
        if color < 3:                      # Green/Yellow are informational, not triggers
            return Trigger.none()
        severity = "severe" if color >= 4 else "high"
        label = COLOR_NAMES.get(color, str(color))
        kind = "nowcast (next 3h)" if t == "nowcast" else "5-day district warning"
        return Trigger(
            fired=True, severity=severity,
            reason=f"IMD {label} alert on {kind} for {obs.district}: {obs.message}",
            contribution=0.30 if color >= 4 else 0.20,
            category="imd_warning",
        )

    if t in ("rainfall", "current_wx"):
        mm = obs.rainfall_mm
        if mm is None or mm < HEAVY_MM:
            return Trigger.none()
        where = obs.district or obs.station_name or "unknown location"
        window = "24h district rainfall" if t == "rainfall" else "last 24h station rainfall"
        return Trigger(
            fired=True, severity=_rainfall_severity(mm),
            reason=f"{window} of {mm} mm at {where} exceeds IMD heavy-rain threshold ({HEAVY_MM} mm)",
            contribution=0.25 if mm < VERY_HEAVY_MM else 0.35,
            category="heavy_rainfall",
        )

    if t == "qpf":
        mm = obs.rainfall_mm     # upper bound of the Day-1 forecast band
        if mm is None or mm < 100:
            return Trigger.none()
        return Trigger(
            fired=True, severity="high" if mm >= 200 else "moderate",
            reason=f"Basin QPF forecasts up to {mm} mm over {obs.basin}/{obs.sub_basin} in 24h",
            contribution=0.15,
            category="basin_forecast",
        )

    if t == "ow_current":
        # Observed rain over the reported window. OpenWeather reports per 1h/3h, so
        # the IMD daily thresholds do not apply directly — a 3h total at or above a
        # quarter of the daily heavy-rain figure is already a serious rate.
        mm = obs.rainfall_mm or 0.0
        if mm >= HEAVY_MM / 4:
            severity = "severe" if mm >= HEAVY_MM else "high" if mm >= HEAVY_MM / 2 else "moderate"
            return Trigger(
                fired=True, severity=severity,
                reason=f"OpenWeather observed {mm} mm of rain at {obs.district} "
                       f"(live station reading, not forecast)",
                contribution=0.30 if severity != "moderate" else 0.20,
                category="observed_rainfall",
            )
        # Storm-favourable atmosphere is supporting evidence only.
        if (obs.pressure_hpa or 1013) < 1000 and (obs.humidity_pct or 0) >= 90:
            return Trigger(
                fired=True, severity="low",
                reason=f"OpenWeather at {obs.district}: {obs.pressure_hpa} hPa with "
                       f"{obs.humidity_pct}% humidity — storm-favourable conditions",
                contribution=0.10, category="atmospheric",
            )
        return Trigger.none()

    if t == "ow_forecast":
        # rainfall_mm on a forecast row is the expected next-24h accumulation, which
        # is exactly what IMD's daily classification is defined against.
        mm = obs.rainfall_mm
        if mm is None or mm < HEAVY_MM:
            return Trigger.none()
        return Trigger(
            fired=True, severity=_rainfall_severity(mm),
            reason=f"OpenWeather forecasts {mm} mm over the next 24h at {obs.district} "
                   f"— exceeds the IMD heavy-rain threshold ({HEAVY_MM} mm)",
            contribution=0.20,
            category="forecast_rainfall",
        )

    if t == "aws":
        # AWS carries no rainfall field in the IMD schema; a deep pressure drop with
        # saturated air is a supporting signal only, never enough to open an event.
        if (obs.pressure_hpa or 1013) < 1000 and (obs.humidity_pct or 0) >= 90:
            return Trigger(
                fired=True, severity="low",
                reason=f"AWS {obs.station_name}: pressure {obs.pressure_hpa} hPa with "
                       f"{obs.humidity_pct}% humidity — storm-favourable conditions",
                contribution=0.10,
                category="atmospheric",
            )
        return Trigger.none()

    return Trigger.none()


def max_severity(a: str, b: str) -> str:
    return a if SEVERITY_ORDER.index(a) >= SEVERITY_ORDER.index(b) else b
