from __future__ import annotations

import asyncio

from livekit_agent.events import log_event, log_note


class TurnAssembler:
    def __init__(self, session_id: str, settle_ms: int = 400) -> None:
        self.session_id = session_id
        self.settle_ms = settle_ms
        self.turn_n = 0
        self._parts: list[str] = []
        self._speaking = False
        self._flush_task: asyncio.Task | None = None

    def on_user_speaking(self) -> None:
        self._speaking = True
        self._cancel_flush()
        log_event("STT", "speech_started", session_id=self.session_id)

    def on_user_stopped(self) -> None:
        self._speaking = False
        log_event("STT", "speech_ended", session_id=self.session_id)
        self._schedule_flush()

    def on_transcript(self, text: str, is_final: bool) -> None:
        text = (text or "").strip()
        if not text:
            return

        if not is_final:
            log_event(
                "STT",
                "interim",
                session_id=self.session_id,
                detail=f"chars={len(text)}",
            )
            return

        self._parts.append(text)
        log_event(
            "STT",
            "final_segment",
            session_id=self.session_id,
            detail=f"chars={len(text)}",
        )
        if not self._speaking:
            self._schedule_flush()

    def _cancel_flush(self) -> None:
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
        self._flush_task = None

    def _schedule_flush(self) -> None:
        self._cancel_flush()
        self._flush_task = asyncio.create_task(self._flush_after_settle())

    async def _flush_after_settle(self) -> None:
        try:
            await asyncio.sleep(self.settle_ms / 1000)
        except asyncio.CancelledError:
            return

        if self._speaking or not self._parts:
            return

        self.turn_n += 1
        turn_id = f"turn_{self.turn_n}"
        text = " ".join(self._parts).strip()
        self._parts = []

        log_event(
            "STT",
            "final_turn",
            session_id=self.session_id,
            turn_id=turn_id,
            detail=f"chars={len(text)}",
        )
        log_note(
            self.session_id,
            f"FINAL PATIENT TURN ({turn_id}):\n{text}",
        )
