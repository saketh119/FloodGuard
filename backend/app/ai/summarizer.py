"""
ai/summarizer.py — AI Summarizer Service.

Uses OpenRouter LLM to generate a natural language summary of a flood event
based on its accumulated evidence.
"""
import httpx
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.models.events import FloodEvent

log = get_logger(__name__)

class AISummarizer:
    
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        # Use a fast/free model for now
        self.model = "google/gemini-flash-1.5" 
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    async def summarize(self, event_id: str):
        """Generates a summary for the given event and updates the database."""
        async with AsyncSessionLocal() as db:
            event = await self._get_event(db, event_id)
            if not event:
                return

            if self.api_key == "dummy" or not self.api_key:
                log.info(f"AI Summarizer: No OpenRouter key. Using stub summary for {event_id[:8]}...")
                event.ai_summary = f"Stub Summary: Flood event detected in {event.district}, {event.state}. Status is {event.status}. Confidence: {event.confidence_score}. Evidence count: {event.evidence_count}."
                await db.commit()
                return

            # Collect evidence context
            context = self._build_context(event)
            summary = await self._call_llm(context)
            
            if summary:
                event.ai_summary = summary
                await db.commit()
                log.info(f"Generated AI summary for event {event_id[:8]}...")

    async def _get_event(self, db, event_id: str) -> FloodEvent | None:
        result = await db.execute(
            select(FloodEvent).options(selectinload(FloodEvent.evidence)).where(FloodEvent.event_id == event_id)
        )
        return result.scalars().first()

    def _build_context(self, event: FloodEvent) -> str:
        lines = [
            f"Location: {event.district}, {event.state}",
            f"Status: {event.status}, Risk Score: {event.risk_score}",
            "Evidence:"
        ]
        for ev in event.evidence:
            lines.append(f"- [{ev.source.upper()}] {ev.trigger_reason}")
        return "\n".join(lines)

    async def _call_llm(self, context: str) -> str | None:
        prompt = f"""
        You are an AI assistant for a Flood Intelligence Platform.
        Summarize the following flood event details into a concise, 2-3 sentence situation report.
        
        {context}
        
        Summary:
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(self.url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                log.error(f"Failed to generate summary: {e}")
                return None
