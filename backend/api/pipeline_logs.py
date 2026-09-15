"""Receive RAG / guidance pipeline events from the LiveKit agent and log them here.

Voice turn/speech logs stay in the agent process. This endpoint only mirrors
retrieval + guidance phases into the FastAPI terminal.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/pipeline", tags=["Pipeline"])

logger = logging.getLogger("healia.rag")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


class PipelineEventIn(BaseModel):
    type: str | None = None
    ts: str | None = None
    session_id: str = "-"
    turn_id: str = "-"
    phase: str
    status: str
    message: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    elapsed_ms: int | None = None


def _compact_data(data: dict[str, Any]) -> str:
    # Drop bulky frontend payload from terminal lines.
    slim = {k: v for k, v in data.items() if k != "results"}
    if "results" in data and isinstance(data["results"], dict):
        slim["results_keys"] = sorted(data["results"].keys())
    compact = json.dumps(slim, ensure_ascii=False, separators=(",", ":"))
    if len(compact) > 280:
        return compact[:277] + "..."
    return compact


@router.post("/events")
async def receive_pipeline_event(event: PipelineEventIn) -> dict[str, str]:
    parts = [
        f"[healia.rag] {event.phase}.{event.status}",
        f"session={event.session_id}",
        f"turn={event.turn_id}",
    ]
    if event.elapsed_ms is not None:
        parts.append(f"elapsed_ms={event.elapsed_ms}")
    if event.message:
        parts.append(event.message)
    if event.data:
        parts.append(f"data={_compact_data(event.data)}")

    logger.info(" | ".join(parts))
    return {"ok": "true"}
