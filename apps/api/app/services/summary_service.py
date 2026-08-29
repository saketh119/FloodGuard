"""AI summariser — rewrites an event's narrative as new evidence attaches.

The summary is regenerated from the event's own evidence trail, so it stays consistent
with what the system can actually justify. No key configured → a deterministic
template summary, which keeps the dashboard populated without inventing anything.
"""
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.models import EventEvidence, FloodEvent, ImdObservation, utcnow
from app.services.llm import LLMUnavailable, generate

log = get_logger("floodguard.summary")

SYSTEM_PROMPT = (
    "You are a flood situation analyst writing for Indian district emergency officers. "
    "Summarise the flood event from the evidence supplied — and ONLY from that evidence. "
    "Write 3-5 sentences covering: what is happening, what the evidence shows, how "
    "confident the assessment is, and the single most important action for officials. "
    "State severity and confidence honestly, including when the evidence is thin. "
    "No preamble, no headings, no invented figures or phone numbers."
)


def _evidence_lines(db: Session, event: FloodEvent) -> list[str]:
    rows = db.execute(
        select(EventEvidence, ImdObservation)
        .join(ImdObservation, EventEvidence.observation_id == ImdObservation.id)
        .where(EventEvidence.event_id == event.id)
        .order_by(EventEvidence.added_at.desc())
    ).all()
    return [
        f"- [{obs.source}/{obs.observation_type} @ {obs.observed_at:%Y-%m-%d}] "
        f"{ev.trigger_reason} (weight {ev.contribution_score})"
        for ev, obs in rows
    ]


def _template_summary(event: FloodEvent, lines: list[str]) -> str:
    prob = (
        f" The severity model puts the chance of escalation to a severe flood at "
        f"{event.prediction_probability:.0%}."
        if event.prediction_probability is not None else ""
    )
    return (
        f"{event.severity.capitalize()} {event.category.replace('_', ' ')} conditions are "
        f"being tracked in {event.district}, {event.state or 'India'}, currently at status "
        f"'{event.status}'. The assessment rests on {len(lines)} corroborating "
        f"observation(s) from IMD, giving a confidence of {event.confidence_score:.0%} and a "
        f"risk score of {event.risk_score}/100.{prob} "
        f"District officials should verify conditions on the ground and follow NDMA flood "
        f"response procedure for a {event.severity} event."
    )


async def summarise_event(db: Session, event: FloodEvent, force: bool = False) -> dict[str, Any]:
    lines = _evidence_lines(db, event)
    if not lines:
        return {"event_uid": event.event_uid, "ai_summary": None,
                "generated": False, "reason": "no evidence attached yet"}

    if event.ai_summary and not force:
        return {"event_uid": event.event_uid, "ai_summary": event.ai_summary,
                "generated": False, "reason": "cached — pass force=true to regenerate"}

    facts = (
        f"District: {event.district}, {event.state or 'unknown state'}\n"
        f"Category: {event.category}\nStatus: {event.status}\nSeverity: {event.severity}\n"
        f"Confidence: {event.confidence_score:.2f}\nRisk score: {event.risk_score}/100\n"
        f"Severe-escalation probability (ML): "
        f"{event.prediction_probability if event.prediction_probability is not None else 'not scored'}\n"
        f"First seen: {event.first_seen:%Y-%m-%d}\nLast updated: {event.last_seen:%Y-%m-%d}\n\n"
        f"Evidence trail:\n" + "\n".join(lines)
    )

    try:
        summary = await generate(prompt=facts, system=SYSTEM_PROMPT, temperature=0.3, max_tokens=600)
        llm_used = True
    except LLMUnavailable as exc:
        level = log.info if exc.reason == "no_key" else log.warning
        level("LLM unavailable, using template summary: %s", exc)
        summary = _template_summary(event, lines)
        llm_used = False

    event.ai_summary = summary
    event.summary_generated_at = utcnow().replace(tzinfo=None)
    event.updated_at = utcnow()
    db.commit()

    return {"event_uid": event.event_uid, "ai_summary": summary,
            "generated": True, "llm_used": llm_used, "evidence_count": len(lines)}
