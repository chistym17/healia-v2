from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from auth.supabase_auth import get_current_user
from db import sessions as session_repo

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])

SessionStatus = Literal["started", "in_progress", "processing", "completed", "failed"]


class TranscriptMessage(BaseModel):
    role: Literal["user", "healia"]
    text: str
    ts: str | None = None


class CreateSessionRequest(BaseModel):
    livekit_room_name: str | None = None
    livekit_session_id: str | None = None
    title: str | None = Field(default=None, max_length=200)
    status: SessionStatus = "started"


class UpdateSessionRequest(BaseModel):
    status: SessionStatus | None = None
    title: str | None = Field(default=None, max_length=200)
    transcript: list[TranscriptMessage] | None = None
    livekit_room_name: str | None = None
    livekit_session_id: str | None = None


class ReferenceItem(BaseModel):
    source: str = ""
    title: str = ""


class UpsertResultsRequest(BaseModel):
    summary: str = ""
    possible_concerns: str = ""
    actions: list[str] = Field(default_factory=list)
    warning_signs: str = ""
    seek_care: str = ""
    references: list[ReferenceItem] = Field(default_factory=list)
    spoken_answer: str | None = None
    confidence: str | None = None
    raw_guidance: dict[str, Any] | None = None
    mark_completed: bool = True


class CompleteSessionRequest(BaseModel):
    title: str | None = None
    transcript: list[TranscriptMessage] | None = None
    results: UpsertResultsRequest


def _serialize(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    out: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, UUID):
            out[key] = str(value)
        elif isinstance(value, datetime):
            out[key] = value.isoformat()
        else:
            out[key] = value
    return out


@router.post("")
def create_session(
    body: CreateSessionRequest,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    row = session_repo.create_session(
        user_id=user["id"],
        livekit_room_name=body.livekit_room_name,
        livekit_session_id=body.livekit_session_id,
        title=body.title,
        status=body.status,
    )
    return {"session": _serialize(row)}


@router.get("")
def list_sessions(
    limit: int = Query(default=50, ge=1, le=100),
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    rows = session_repo.list_sessions(user["id"], limit=limit)
    return {"sessions": [_serialize(r) for r in rows]}


@router.get("/{session_id}")
def get_session(
    session_id: str,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    payload = session_repo.get_session_with_results(session_id, user["id"])
    if not payload:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session": _serialize(payload["session"]),
        "results": _serialize(payload["results"]),
    }


@router.patch("/{session_id}")
def update_session(
    session_id: str,
    body: UpdateSessionRequest,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    transcript = None
    if body.transcript is not None:
        transcript = [m.model_dump() for m in body.transcript]
    row = session_repo.update_session(
        session_id,
        user["id"],
        status=body.status,
        title=body.title,
        transcript=transcript,
        livekit_room_name=body.livekit_room_name,
        livekit_session_id=body.livekit_session_id,
        completed=body.status == "completed",
    )
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session": _serialize(row)}


@router.put("/{session_id}/results")
def upsert_results(
    session_id: str,
    body: UpsertResultsRequest,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    results = session_repo.upsert_results(
        session_id,
        user["id"],
        summary=body.summary,
        possible_concerns=body.possible_concerns,
        actions=body.actions,
        warning_signs=body.warning_signs,
        seek_care=body.seek_care,
        references=[r.model_dump() for r in body.references],
        spoken_answer=body.spoken_answer,
        confidence=body.confidence,
        raw_guidance=body.raw_guidance,
    )
    if not results:
        raise HTTPException(status_code=404, detail="Session not found")

    session = None
    if body.mark_completed:
        session = session_repo.update_session(
            session_id,
            user["id"],
            status="completed",
            completed=True,
        )

    return {
        "results": _serialize(results),
        "session": _serialize(session)
        if session
        else _serialize(session_repo.get_session(session_id, user["id"])),
    }


@router.post("/{session_id}/complete")
def complete_session(
    session_id: str,
    body: CompleteSessionRequest,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    transcript = None
    if body.transcript is not None:
        transcript = [m.model_dump() for m in body.transcript]

    session = session_repo.update_session(
        session_id,
        user["id"],
        status="completed",
        title=body.title,
        transcript=transcript,
        completed=True,
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    results = session_repo.upsert_results(
        session_id,
        user["id"],
        summary=body.results.summary,
        possible_concerns=body.results.possible_concerns,
        actions=body.results.actions,
        warning_signs=body.results.warning_signs,
        seek_care=body.results.seek_care,
        references=[r.model_dump() for r in body.results.references],
        spoken_answer=body.results.spoken_answer,
        confidence=body.results.confidence,
        raw_guidance=body.results.raw_guidance,
    )
    return {
        "session": _serialize(session),
        "results": _serialize(results),
    }


@router.delete("/{session_id}")
def delete_session(
    session_id: str,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    ok = session_repo.delete_session(session_id, user["id"])
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted"}
