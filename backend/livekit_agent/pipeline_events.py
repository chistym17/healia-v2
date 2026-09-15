"""Structured Healia pipeline events for logs and optional frontend delivery."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from collections import deque
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any

from livekit_agent import config
from livekit_agent.events import log_event

_log = logging.getLogger("healia.pipeline")

if not _log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    _log.addHandler(handler)
    _log.setLevel(logging.INFO)
    _log.propagate = False

PIPELINE_TOPIC = "healia.pipeline"
MAX_HISTORY = 200

Publisher = Callable[[dict[str, Any]], Awaitable[None] | None]

_lock = threading.Lock()
_publishers: dict[str, Publisher] = {}
_history: dict[str, deque[dict[str, Any]]] = {}


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def register_pipeline_publisher(session_id: str, publisher: Publisher) -> None:
    with _lock:
        _publishers[session_id] = publisher


def unregister_pipeline_publisher(session_id: str) -> None:
    with _lock:
        _publishers.pop(session_id, None)
        _history.pop(session_id, None)


def get_pipeline_history(session_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
    with _lock:
        items = list(_history.get(session_id, ()))
    return items[-limit:]


def _summarize_chunks(chunks: list[dict[str, Any]], *, limit: int = 3) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for hit in chunks[:limit]:
        meta = hit.get("metadata") or {}
        summary.append(
            {
                "id": hit.get("id"),
                "source": hit.get("source"),
                "topic": meta.get("topic"),
                "section": meta.get("section"),
                "score": hit.get("rerank_score", hit.get("score")),
            }
        )
    return summary


def _schedule_publish(session_id: str, event: dict[str, Any]) -> None:
    with _lock:
        publisher = _publishers.get(session_id)
    if publisher is None:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    async def _run() -> None:
        try:
            result = publisher(event)
            if asyncio.iscoroutine(result):
                await result
        except Exception as exc:
            log_event(
                "PIPELINE",
                "publish_error",
                session_id=session_id,
                turn_id=str(event.get("turn_id") or "-"),
                detail=str(exc),
            )

    loop.create_task(_run())


def emit_pipeline_event(
    *,
    session_id: str,
    turn_id: str,
    phase: str,
    status: str,
    message: str,
    data: dict[str, Any] | None = None,
    elapsed_ms: int | None = None,
) -> dict[str, Any]:
    """
    Emit a structured pipeline event.

    - Logs a human-readable line via log_event
    - Logs JSON on the healia.pipeline logger (for grep / log shippers)
    - Stores per-session history (for debugging / future HTTP poll)
    - Publishes to a registered session publisher (e.g. LiveKit data channel)
    """
    if not config.PIPELINE_EVENTS_ENABLED:
        return {}

    payload = dict(data or {})
    event: dict[str, Any] = {
        "type": "healia.pipeline",
        "ts": _utc_iso(),
        "session_id": session_id,
        "turn_id": turn_id,
        "phase": phase,
        "status": status,
        "message": message,
        "data": payload,
    }
    if elapsed_ms is not None:
        event["elapsed_ms"] = elapsed_ms

    detail_parts = [f"status={status}", f"msg={message}"]
    if elapsed_ms is not None:
        detail_parts.append(f"elapsed_ms={elapsed_ms}")
    if payload:
        compact = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        if len(compact) > 240:
            compact = compact[:237] + "..."
        detail_parts.append(f"data={compact}")

    log_event(
        "PIPELINE",
        f"{phase}.{status}",
        session_id=session_id,
        turn_id=turn_id,
        detail=" | ".join(detail_parts),
    )

    if config.PIPELINE_EVENTS_LOG_JSON:
        _log.info(json.dumps(event, ensure_ascii=False))

    with _lock:
        if session_id not in _history:
            _history[session_id] = deque(maxlen=MAX_HISTORY)
        _history[session_id].append(event)

    if config.PIPELINE_EVENTS_TO_ROOM:
        _schedule_publish(session_id, event)

    return event


def assessment_completed_event(
    evidence: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    suggestions = evidence.get("suggested_questions") or []
    topics = [s.get("topic") for s in suggestions if s.get("topic")]
    return (
        f"Found {len(suggestions)} assessment suggestions",
        {
            "source": evidence.get("source"),
            "pack": evidence.get("pack"),
            "suggestion_count": len(suggestions),
            "topics": topics[:5],
            "query": evidence.get("query"),
        },
    )


def knowledge_retrieval_completed_event(
    retrieval: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    chunks = retrieval.get("chunks") or []
    topics = []
    for hit in chunks[:5]:
        meta = hit.get("metadata") or {}
        topic = meta.get("topic")
        if topic:
            topics.append(topic)
    mode = retrieval.get("mode") or retrieval.get("requested_mode")
    msg = f"Retrieved {len(chunks)} medical references"
    if retrieval.get("error"):
        msg = f"Retrieval failed: {retrieval['error']}"
    elif not chunks:
        msg = "No medical references found"
    return (
        msg,
        {
            "source": retrieval.get("source"),
            "mode": mode,
            "requested_mode": retrieval.get("requested_mode"),
            "chunk_count": len(chunks),
            "top_topics": topics,
            "fallback": retrieval.get("fallback"),
            "error": retrieval.get("error"),
            "top_hits": _summarize_chunks(chunks),
        },
    )


def guidance_completed_event(
    guidance: dict[str, Any] | None,
    *,
    error: str | None = None,
) -> tuple[str, dict[str, Any]]:
    if error or not guidance:
        return (
            f"Guidance failed: {error or 'unknown'}",
            {"error": error or "unknown", "confidence": None},
        )
    spoken = str(guidance.get("spoken_answer") or "")
    citations = guidance.get("citations") or []
    confidence = guidance.get("confidence")
    # Full Results payload for the frontend (v2 Results page).
    results = {
        "summary": guidance.get("summary") or "",
        "possible_concerns": guidance.get("possible_concerns") or "",
        "actions": guidance.get("actions") or [],
        "warning_signs": guidance.get("warning_signs") or "",
        "seek_care": guidance.get("seek_care") or "",
        "spoken_answer": spoken,
        "detailed_answer": guidance.get("detailed_answer") or spoken,
        "citations": citations[:10] if isinstance(citations, list) else [],
        "confidence": confidence,
    }
    return (
        f"Guidance ready ({confidence or 'unknown'} confidence)",
        {
            "confidence": confidence,
            "spoken_chars": len(spoken),
            "citation_count": len(citations) if isinstance(citations, list) else 0,
            "citations": citations[:5] if isinstance(citations, list) else [],
            "results": results,
        },
    )
