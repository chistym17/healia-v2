from __future__ import annotations

import json
import time

from livekit_agent import config
from livekit_agent.controller import validate_and_apply
from livekit_agent.events import log_event, log_note
from livekit_agent.state import ConsultationState
from livekit_agent.supervisor import run_supervisor


async def handle_patient_turn(
    session_id: str,
    turn_id: str,
    patient_text: str,
    state: ConsultationState,
) -> None:
    """Part 3 step 1: supervisor + validation + logs. Voice unchanged until step 2."""
    if not config.SUPERVISOR_ENABLED:
        return

    log_event(
        "SUP",
        "supervisor_started",
        session_id=session_id,
        turn_id=turn_id,
        detail=f"mode={config.SUPERVISOR_MODE}",
    )
    started = time.monotonic()

    try:
        decision = await run_supervisor(
            patient_turn=patient_text,
            state=state.snapshot(),
        )
    except Exception as exc:
        log_event(
            "SUP",
            "supervisor_error",
            session_id=session_id,
            turn_id=turn_id,
            detail=str(exc),
        )
        log_event(
            "CTRL",
            "decision_validated",
            session_id=session_id,
            turn_id=turn_id,
            detail="ok=false error=supervisor_failed",
        )
        return

    elapsed_ms = int((time.monotonic() - started) * 1000)
    log_event(
        "SUP",
        "decision",
        session_id=session_id,
        turn_id=turn_id,
        detail=(
            f"action={decision.action} confidence={decision.confidence:.2f} "
            f"elapsed_ms={elapsed_ms}"
        ),
    )

    result = validate_and_apply(state, decision)
    if result.ok:
        log_event(
            "CTRL",
            "decision_validated",
            session_id=session_id,
            turn_id=turn_id,
            detail="ok=true",
        )
        log_event(
            "CTRL",
            "state_committed",
            session_id=session_id,
            turn_id=turn_id,
            detail=f"phase={state.phase} followups={state.followup_count}",
        )
    else:
        log_event(
            "CTRL",
            "decision_validated",
            session_id=session_id,
            turn_id=turn_id,
            detail=f"ok=false error={result.error}",
        )
        return

    log_note(
        session_id,
        "\n".join(
            [
                f"SUPERVISOR DECISION ({turn_id}):",
                f"action: {decision.action}",
                f"spoken_utterance: {decision.spoken_utterance}",
                f"followup_topic: {decision.followup_topic or '-'}",
                f"reason: {decision.reason or '-'}",
                f"state: {json.dumps(state.snapshot(), ensure_ascii=False)}",
            ]
        ),
    )

    if config.SUPERVISOR_MODE == "log_only":
        log_event(
            "CTRL",
            "speech_deferred",
            session_id=session_id,
            turn_id=turn_id,
            detail="step1_log_only voice still gemini_auto",
        )
