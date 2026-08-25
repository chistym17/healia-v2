from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from livekit_agent.events import log_event

if TYPE_CHECKING:
    from livekit.agents import AgentSession


class TurnCoordinator:
    """Cancel in-flight supervisor + speech when user barges in or a new turn starts."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self._active: asyncio.Task | None = None
        self._active_turn_id: str | None = None

    def has_active(self) -> bool:
        return self._active is not None and not self._active.done()

    async def cancel_active(
        self,
        session: AgentSession | None,
        *,
        reason: str,
        turn_id: str | None = None,
    ) -> None:
        cancelled = False
        tid = turn_id or self._active_turn_id

        if self._active and not self._active.done():
            self._active.cancel()
            cancelled = True
            try:
                await self._active
            except asyncio.CancelledError:
                pass

        self._active = None
        self._active_turn_id = None

        if cancelled and tid:
            log_event(
                "CTRL",
                "turn_cancelled",
                session_id=self.session_id,
                turn_id=tid,
                detail=f"reason={reason}",
            )

        if session is not None:
            try:
                await session.interrupt(force=True)
            except RuntimeError:
                pass

    async def run_turn(
        self,
        turn_id: str,
        session: AgentSession | None,
        work: Callable[[], Awaitable[None]],
    ) -> None:
        if self.has_active():
            await self.cancel_active(
                session,
                reason="superseded",
                turn_id=self._active_turn_id,
            )

        async def _wrapped() -> None:
            await work()

        self._active_turn_id = turn_id
        self._active = asyncio.create_task(_wrapped())
        try:
            await self._active
        finally:
            if self._active is not None and self._active.done():
                self._active = None
                if self._active_turn_id == turn_id:
                    self._active_turn_id = None
