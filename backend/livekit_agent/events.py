from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

_log = logging.getLogger("healia.events")

if not _log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    _log.addHandler(handler)
    _log.setLevel(logging.INFO)
    _log.propagate = False

LOGS_DIR = Path(__file__).resolve().parents[2] / "logs"

_lock = threading.Lock()
_session_paths: dict[str, Path] = {}
_session_seq: dict[str, int] = {}


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]


def _next_file_number() -> int:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    numbers = []
    for path in LOGS_DIR.glob("*.log"):
        prefix = path.name.split("_", 1)[0]
        if prefix.isdigit():
            numbers.append(int(prefix))
    return (max(numbers) + 1) if numbers else 1


def start_session_log(session_id: str, *, room: str = "", model: str = "") -> Path:
    with _lock:
        n = _next_file_number()
        path = LOGS_DIR / f"{n:03d}_{session_id}.log"
        _session_paths[session_id] = path
        _session_seq[session_id] = 0

        header = [
            f"# Healia session log",
            f"# file={path.name}",
            f"# session_id={session_id}",
            f"# room={room or '-'}",
            f"# model={model or '-'}",
            f"# started_utc={datetime.now(timezone.utc).isoformat()}",
            f"#",
        ]
        path.write_text("\n".join(header) + "\n", encoding="utf-8")
        return path


def _append(session_id: str, line: str) -> None:
    path = _session_paths.get(session_id)
    if path is None:
        return
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def log_event(
    stage: str,
    event: str,
    *,
    session_id: str = "-",
    turn_id: str = "-",
    detail: str = "",
) -> None:
    with _lock:
        seq = _session_seq.get(session_id, 0) + 1
        if session_id in _session_seq:
            _session_seq[session_id] = seq

    body = (
        f"[healia] {_ts()} | {session_id} | {turn_id} | {stage} | {event}"
        + (f" | {detail}" if detail else "")
    )
    line = f"{seq} | {body}" if session_id in _session_paths else body
    _log.info(line)
    if session_id in _session_paths:
        _append(session_id, line)


def log_note(session_id: str, text: str) -> None:
    """Write free-form analysis notes (e.g. full transcript) to terminal + file."""
    with _lock:
        seq = _session_seq.get(session_id, 0) + 1
        if session_id in _session_seq:
            _session_seq[session_id] = seq

    for raw in text.strip().splitlines() or [text]:
        line = f"{seq} | {raw}" if session_id in _session_paths else raw
        _log.info(line)
        if session_id in _session_paths:
            _append(session_id, line)
