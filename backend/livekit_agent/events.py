from __future__ import annotations

import logging
from datetime import datetime, timezone

_log = logging.getLogger("healia.events")

if not _log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    _log.addHandler(handler)
    _log.setLevel(logging.INFO)
    _log.propagate = False


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]


def log_event(
    stage: str,
    event: str,
    *,
    session_id: str = "-",
    turn_id: str = "-",
    detail: str = "",
) -> None:
    line = (
        f"[healia] {_ts()} | {session_id} | {turn_id} | {stage} | {event}"
        + (f" | {detail}" if detail else "")
    )
    _log.info(line)
