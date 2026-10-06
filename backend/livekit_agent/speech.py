"""Controlled agent speech — exact text, one utterance at a time."""

from __future__ import annotations

import asyncio
from typing import Any

from livekit.agents import AgentSession

from livekit_agent.events import log_event
from livekit_agent.supervisor import SupervisorDecision

# Per-session lock so two pipeline paths never speak over each other.
_speech_locks: dict[str, asyncio.Lock] = {}
_active_handles: dict[str, Any] = {}


def _lock_for(session_id: str) -> asyncio.Lock:
    lock = _speech_locks.get(session_id)
    if lock is None:
        lock = asyncio.Lock()
        _speech_locks[session_id] = lock
    return lock


async def interrupt_speech(
    session: AgentSession | None,
    *,
    session_id: str = "-",
) -> None:
    """Stop anything currently queued/playing for this session."""
    handle = _active_handles.pop(session_id, None)
    if handle is not None:
        try:
            handle.interrupt(force=True)
        except Exception:
            pass
    if session is not None:
        try:
            await session.interrupt(force=True)
        except RuntimeError:
            pass
        except Exception:
            pass
    # Brief settle so Gemini/LiveKit can drop the prior generation.
    await asyncio.sleep(0.08)


async def _speak_exact(
    session: AgentSession,
    text: str,
    *,
    session_id: str,
    turn_id: str,
    kind: str,
) -> None:
    text = (text or "").strip()
    if not text:
        return

    async with _lock_for(session_id):
        await interrupt_speech(session, session_id=session_id)

        last_error: BaseException | None = None
        for attempt in (1, 2):
            handle = None
            try:
                handle = session.generate_reply(
                    instructions=(
                        "Say exactly the following to the patient. "
                        "Do not add, omit, or ask anything else:\n\n"
                        f"{text}"
                    ),
                    tool_choice="none",
                )
                _active_handles[session_id] = handle
                await handle.wait_for_playout()

                if handle.interrupted:
                    log_event(
                        "VOICE",
                        "speech_interrupted",
                        session_id=session_id,
                        turn_id=turn_id,
                        detail=f"kind={kind} attempt={attempt}",
                    )
                    return

                err = None
                try:
                    err = handle.exception()
                except Exception:
                    err = None

                if err is not None:
                    last_error = err
                    log_event(
                        "VOICE",
                        "speech_attempt_failed",
                        session_id=session_id,
                        turn_id=turn_id,
                        detail=f"kind={kind} attempt={attempt} error={err}",
                    )
                    await interrupt_speech(session, session_id=session_id)
                    continue

                log_event(
                    "VOICE",
                    "speech_playout_done",
                    session_id=session_id,
                    turn_id=turn_id,
                    detail=f"kind={kind} attempt={attempt} chars={len(text)}",
                )
                return
            except asyncio.CancelledError:
                await interrupt_speech(session, session_id=session_id)
                raise
            except Exception as exc:
                last_error = exc
                log_event(
                    "VOICE",
                    "speech_attempt_failed",
                    session_id=session_id,
                    turn_id=turn_id,
                    detail=f"kind={kind} attempt={attempt} error={exc}",
                )
                await interrupt_speech(session, session_id=session_id)
            finally:
                if handle is not None and _active_handles.get(session_id) is handle:
                    _active_handles.pop(session_id, None)

        if last_error is not None:
            raise RuntimeError(f"speech_failed:{last_error}") from last_error


async def speak_guidance(
    session: AgentSession,
    guidance: dict,
    *,
    session_id: str = "-",
    turn_id: str = "-",
) -> None:
    """Speak a grounded knowledge-guidance answer (voice-friendly)."""
    text = str(guidance.get("spoken_answer") or "").strip()
    if not text:
        return
    await _speak_exact(
        session,
        text,
        session_id=session_id,
        turn_id=turn_id,
        kind="guidance",
    )


async def speak_decision(
    session: AgentSession,
    decision: SupervisorDecision,
    *,
    session_id: str = "-",
    turn_id: str = "-",
) -> None:
    if not decision.spoken_utterance.strip():
        return
    await _speak_exact(
        session,
        decision.spoken_utterance,
        session_id=session_id,
        turn_id=turn_id,
        kind="supervisor",
    )


async def speak_text(
    session: AgentSession,
    text: str,
    *,
    session_id: str = "-",
    turn_id: str = "-",
    kind: str = "system",
) -> None:
    await _speak_exact(
        session,
        text,
        session_id=session_id,
        turn_id=turn_id,
        kind=kind,
    )
