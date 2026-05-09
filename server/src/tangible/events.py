"""In-process pub/sub broker for Server-Sent Events.

A single-process deployment (uvicorn + FastAPI) is assumed; events are
broadcast via asyncio.Queue objects held in memory.  If the deployment
ever moves to multiple workers, replace this module with a Redis Pub/Sub
or similar backend.

Usage (server side, publishing)
--------------------------------
from tangible.events import publish_event
publish_event(collection_id, "item-added", {"id": item.id, "title": item.title})

Usage (server side, subscribing — inside an async endpoint)
------------------------------------------------------------
from tangible.events import subscribe, unsubscribe
queue = subscribe(collection_id)
try:
    while True:
        event = await asyncio.wait_for(queue.get(), timeout=30)
        yield f"data: {event}\\n\\n"
finally:
    unsubscribe(collection_id, queue)
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict

log = logging.getLogger(__name__)

# collection_id -> set of subscriber queues
_subscribers: dict[str, set[asyncio.Queue[str]]] = defaultdict(set)


def subscribe(collection_id: str) -> asyncio.Queue[str]:
    """Register a new subscriber queue for *collection_id* and return it."""
    q: asyncio.Queue[str] = asyncio.Queue(maxsize=64)
    _subscribers[collection_id].add(q)
    return q


def unsubscribe(collection_id: str, queue: asyncio.Queue[str]) -> None:
    """Remove *queue* from the subscriber set for *collection_id*."""
    _subscribers[collection_id].discard(queue)
    if not _subscribers[collection_id]:
        del _subscribers[collection_id]


def publish_event(collection_id: str, event_type: str, data: dict) -> None:
    """Publish an SSE event to all subscribers of *collection_id*.

    This is called from synchronous FastAPI route handlers; it uses
    ``asyncio.get_event_loop().call_soon_threadsafe`` if the running loop is
    not the same thread, but since FastAPI/uvicorn runs everything on one
    event loop thread this is a simple non-blocking put.
    """
    if collection_id not in _subscribers:
        return
    payload = json.dumps({"type": event_type, **data})
    dead: list[asyncio.Queue[str]] = []
    for q in list(_subscribers[collection_id]):
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            # Slow subscriber — drop the event rather than blocking.
            log.debug("SSE queue full for collection %s, dropping event", collection_id)
        except Exception:
            dead.append(q)
    for q in dead:
        _subscribers[collection_id].discard(q)
