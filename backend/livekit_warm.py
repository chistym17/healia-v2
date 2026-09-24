"""Non-blocking LiveKit agent warm (scale-from-zero) after auth."""

from __future__ import annotations

import asyncio
import logging
import os
import uuid

from livekit import api

logger = logging.getLogger(__name__)

AGENT_NAME = "healia"
PREWARM_METADATA = '{"purpose":"prewarm"}'


def agent_warm_enabled() -> bool:
    raw = (os.getenv("LIVEKIT_AGENT_WARM") or "true").strip().lower()
    return raw not in ("0", "false", "no", "off")


async def _warm_agent_async() -> None:
    livekit_url = (os.getenv("LIVEKIT_URL") or "").strip()
    api_key = (os.getenv("LIVEKIT_API_KEY") or "").strip()
    api_secret = (os.getenv("LIVEKIT_API_SECRET") or "").strip()
    if not livekit_url or not api_key or not api_secret:
        logger.warning("agent warm skipped: LiveKit env missing")
        return

    room_name = f"healia-warm-{uuid.uuid4().hex[:10]}"
    async with api.LiveKitAPI(livekit_url, api_key, api_secret) as lk:
        await lk.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                empty_timeout=60,
                max_participants=2,
            )
        )
        await lk.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=AGENT_NAME,
                room=room_name,
                metadata=PREWARM_METADATA,
            )
        )
    logger.info("agent warm dispatched room=%s", room_name)


def warm_livekit_agent() -> None:
    """Sync entry for FastAPI BackgroundTasks — never raises to the caller."""
    if not agent_warm_enabled():
        return
    try:
        asyncio.run(_warm_agent_async())
    except Exception:
        logger.exception("agent warm failed (ignored)")
