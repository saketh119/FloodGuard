"""Request/response models for the public API."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EvidenceOut(BaseModel):
    id: int
    source: str
    observation_id: int
    trigger_reason: str
    contribution_score: float
    added_at: datetime
    observation_type: str | None = None
    observed_at: datetime | None = None

    model_config = {"from_attributes": True}


class EventOut(BaseModel):
    id: int
    event_uid: str
    district: str
    state: str | None
    latitude: float | None
    longitude: float | None
    category: str
    status: str
    severity: str
    confidence_score: float
    risk_score: float
    prediction_probability: float | None
    ai_summary: str | None
    first_seen: datetime
    last_seen: datetime
    evidence_count: int = 0

    model_config = {"from_attributes": True}


class EventDetailOut(EventOut):
    evidence: list[EvidenceOut] = []


class StationOut(BaseModel):
    station_code: str
    station_name: str
    district: str | None
    state: str | None
    latitude: float | None
    longitude: float | None
    source: str

    model_config = {"from_attributes": True}


class ObservationOut(BaseModel):
    id: int
    source: str
    observation_type: str
    district: str | None
    state: str | None
    station_name: str | None
    observed_at: datetime
    color_code: int | None
    rainfall_mm: float | None
    temperature_c: float | None
    humidity_pct: float | None
    message: str | None

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    # 1, not 3: 'Hi' is a legitimate thing to send an assistant, and rejecting it
    # with a validation error is a worse answer than a greeting.
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=12)


class Citation(BaseModel):
    title: str
    page: int | None = None
    source_org: str | None = None
    source_file: str | None = None
    relevance: float | None = None


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    grounded: bool
    llm_used: bool
    llm_error: str | None = None
    # Machine-readable tag: no_key | bad_key | bad_model | rate_limited | blocked | ...
    llm_error_reason: str | None = None
    # True when the input was a greeting rather than a document question.
    conversational: bool = False


class IngestReport(BaseModel):
    fetched: dict[str, int]
    stored: dict[str, int]
    triggered: int
    events_created: int
    evidence_attached: int
    events_resolved: int
    events_scored: int = 0
    summaries_generated: int = 0
    prediction_error: str | None = None


class PredictionOut(BaseModel):
    event_id: int
    event_uid: str
    district: str
    severe_escalation_probability: float
    risk_band: str
    risk_score: float
    confidence_score: float
    model_version: str | None
    model_cv_roc_auc: float | None
    features: dict[str, Any]
    feature_provenance: dict[str, str]
    caveat: str | None
