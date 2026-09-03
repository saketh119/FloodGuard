"""Gemini client.

A thin REST wrapper rather than an SDK: one dependency less, and the surface we need
is a single generateContent POST.

Two behaviours matter here. Every caller degrades gracefully when no key is set, so
the platform demos without one. But when a key IS set and the call fails, the reason
is carried all the way to the caller — a mistyped key, a wrong model name or an
exhausted quota must never look like "no key configured".
"""
import asyncio
from typing import Any

import httpx

from app.core.config import settings
from app.core.logger import get_logger

log = get_logger("floodguard.llm")

# Transient upstream states worth a second attempt: rate limit, overloaded, gateway.
RETRY_STATUS = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 3


class LLMUnavailable(RuntimeError):
    """No key configured, or Gemini could not produce an answer.

    `reason` is a short machine-readable tag; str(exc) is the human explanation.
    """

    def __init__(self, message: str, reason: str = "error"):
        super().__init__(message)
        self.reason = reason


def _api_error(res: httpx.Response) -> tuple[str, str]:
    """Pull Google's actual error text out of the response.

    Google returns {"error": {"code", "message", "status"}}. Surfacing that message
    is the difference between "Gemini returned 400" and "API key not valid".
    """
    try:
        err = res.json().get("error", {})
        message = err.get("message") or res.text[:300]
        status = err.get("status") or ""
    except Exception:
        message, status = res.text[:300], ""

    code = res.status_code
    if code in (401, 403) or "API_KEY_INVALID" in status or "API key not valid" in message:
        return f"Gemini rejected the API key: {message}", "bad_key"
    if code == 404:
        return (f"Model '{settings.GEMINI_MODEL}' was not found. Check GEMINI_MODEL "
                f"in apps/api/.env — Google's reply: {message}"), "bad_model"
    if code == 429:
        return f"Gemini quota or rate limit reached: {message}", "rate_limited"
    return f"Gemini returned HTTP {code}: {message}", "http_error"


def _extract_text(body: dict[str, Any]) -> str:
    """Gemini returns a parts array; thinking models can emit parts without text."""
    for candidate in body.get("candidates") or []:
        parts = (candidate.get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts).strip()
        if text:
            return text
    return ""


def _empty_reason(body: dict[str, Any]) -> tuple[str, str]:
    """A 200 with no text is usually a safety block or a truncated response."""
    if (block := (body.get("promptFeedback") or {}).get("blockReason")):
        return f"Gemini blocked the prompt ({block}).", "blocked"

    candidates = body.get("candidates") or []
    finish = candidates[0].get("finishReason") if candidates else None
    if finish == "MAX_TOKENS":
        return ("Gemini hit the output limit before writing any text. "
                "Raise max_tokens or shorten the context."), "truncated"
    if finish == "SAFETY":
        return "Gemini blocked the response on safety grounds.", "blocked"
    return f"Gemini returned no text (finishReason={finish}).", "empty"


async def generate(prompt: str, system: str | None = None, temperature: float = 0.2,
                   max_tokens: int = 2048) -> str:
    if not settings.llm_enabled:
        raise LLMUnavailable(
            "GEMINI_API_KEY is not set in apps/api/.env", "no_key"
        )

    url = f"{settings.GEMINI_BASE_URL}/models/{settings.GEMINI_MODEL}:generateContent"
    payload: dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            # These are short grounded answers; without this the thinking budget can
            # consume the whole output allowance before any text is emitted.
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}

    headers = {"x-goog-api-key": settings.GEMINI_API_KEY, "Content-Type": "application/json"}
    last_error: LLMUnavailable | None = None

    async with httpx.AsyncClient(timeout=60.0) as client:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                res = await client.post(url, json=payload, headers=headers)
            except httpx.RequestError as exc:
                last_error = LLMUnavailable(
                    f"Could not reach Gemini: {exc.__class__.__name__}", "unreachable"
                )
                if attempt < MAX_ATTEMPTS:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise last_error

            # Models that predate thinkingConfig — and Pro, which forbids a 0 budget —
            # reject it. Drop the field and try once more before giving up.
            if res.status_code == 400 and "thinking" in res.text.lower():
                payload["generationConfig"].pop("thinkingConfig", None)
                log.info("Retrying without thinkingConfig for %s", settings.GEMINI_MODEL)
                res = await client.post(url, json=payload, headers=headers)

            if res.status_code in RETRY_STATUS and attempt < MAX_ATTEMPTS:
                wait = 2 ** attempt
                log.warning("Gemini %s — retrying in %ss (attempt %s/%s)",
                            res.status_code, wait, attempt, MAX_ATTEMPTS)
                await asyncio.sleep(wait)
                continue

            if res.status_code != 200:
                message, reason = _api_error(res)
                log.warning("Gemini call failed: %s", message)
                raise LLMUnavailable(message, reason)

            body = res.json()
            if text := _extract_text(body):
                return text

            message, reason = _empty_reason(body)
            log.warning("Gemini produced no text: %s", message)
            raise LLMUnavailable(message, reason)

    raise last_error or LLMUnavailable("Gemini call failed", "error")


async def probe() -> dict[str, Any]:
    """Make one cheap real call so a misconfigured key surfaces immediately.

    Used by GET /llm/check and `python run.py doctor`. Worth having: without it a bad
    key looks identical to no key at all — both just fall back to extractive answers.
    """
    import time

    if not settings.llm_enabled:
        return {"ok": False, "reason": "no_key", "model": settings.GEMINI_MODEL,
                "error": "GEMINI_API_KEY is not set in apps/api/.env"}

    started = time.perf_counter()
    try:
        text = await generate("Reply with the single word: ready", max_tokens=32)
    except LLMUnavailable as exc:
        return {"ok": False, "reason": exc.reason, "model": settings.GEMINI_MODEL,
                "error": str(exc)}

    return {
        "ok": True, "reason": "ok", "model": settings.GEMINI_MODEL,
        "latency_ms": round((time.perf_counter() - started) * 1000),
        "sample": text[:80],
    }


def key_fingerprint(key: str | None = None) -> str | None:
    """First 8 hex of sha256(key).

    Lets `run.py doctor` tell whether the running process is using the key that is
    currently in .env — settings are read once at import, so editing .env under a
    live server silently changes nothing. Not reversible, safe to log or serve.
    """
    import hashlib

    key = settings.GEMINI_API_KEY if key is None else key
    return hashlib.sha256(key.encode()).hexdigest()[:8] if key else None


def status() -> dict[str, Any]:
    return {
        "provider": "google-gemini",
        "model": settings.GEMINI_MODEL,
        "configured": settings.llm_enabled,
        "key_source": "apps/api/.env → GEMINI_API_KEY",
        "key_fingerprint": key_fingerprint(),
    }
