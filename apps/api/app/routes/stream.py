"""Server-sent events — the dashboard learns about new data the moment it lands.

Polling every 30s means the UI can be half a minute stale and every client burns a
request whether or not anything changed. The collection pipeline already knows when
it has produced something; this lets it say so.

SSE rather than WebSockets: the traffic is one-directional, it survives proxies as
plain HTTP, and the browser reconnects on its own.
"""
import asyncio
import json
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.core.logger import get_logger

log = get_logger("floodguard.stream")
router = APIRouter(tags=["realtime"])

# One queue per connected browser. Bounded so a stalled client cannot grow without
# limit — if it falls behind, it loses updates rather than the server losing memory.
_subscribers: set[asyncio.Queue] = set()
QUEUE_SIZE = 8
HEARTBEAT_S = 20


def publish(event: str, payload: dict[str, Any]) -> None:
    """Fan an event out to every connected client. Never blocks, never raises."""
    if not _subscribers:
        return
    message = {"event": event, "data": payload}
    for queue in list(_subscribers):
        try:
            queue.put_nowait(message)
        except asyncio.QueueFull:
            pass          # slow client: drop this update, keep the connection


def subscriber_count() -> int:
    return len(_subscribers)


@router.get("/stream")
async def stream(request: Request):
    """Long-lived SSE connection. Emits `cycle` after each collection pass."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=QUEUE_SIZE)
    _subscribers.add(queue)
    log.info("SSE client connected (%s total)", len(_subscribers))

    async def events():
        try:
            yield f"event: ready\ndata: {json.dumps({'ok': True})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_S)
                except asyncio.TimeoutError:
                    # Comment frame: keeps proxies from closing an idle connection.
                    yield ": keep-alive\n\n"
                    continue
                yield f"event: {message['event']}\ndata: {json.dumps(message['data'], default=str)}\n\n"
        finally:
            _subscribers.discard(queue)
            log.info("SSE client disconnected (%s remaining)", len(_subscribers))

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",     # tell nginx not to buffer the stream
        },
    )
