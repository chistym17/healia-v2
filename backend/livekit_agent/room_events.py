"""Publish pipeline events to the LiveKit room data channel (frontend can subscribe later)."""

from __future__ import annotations

import json
from typing import Any

from livekit import rtc

from livekit_agent.pipeline_events import PIPELINE_TOPIC


async def publish_pipeline_event_to_room(
    room: rtc.Room,
    event: dict[str, Any],
) -> None:
    local = room.local_participant
    if local is None:
        return
    payload = json.dumps(event, ensure_ascii=False).encode("utf-8")
    await local.publish_data(payload, topic=PIPELINE_TOPIC, reliable=True)
