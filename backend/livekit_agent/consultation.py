from __future__ import annotations

import asyncio
import json
import time
from typing import TYPE_CHECKING

from livekit_agent import config
from livekit_agent.assessment_rag import search as assessment_search
from livekit_agent.case_package import build_case_package
from livekit_agent.controller import validate_and_apply
from livekit_agent.events import log_event, log_note
from livekit_agent.guidance_pipeline import run_knowledge_guidance
from livekit_agent.pipeline_events import (
    assessment_completed_event,
    emit_pipeline_event,
)
from livekit_agent.speech import speak_decision, speak_guidance
from livekit_agent.state import ConsultationState
from livekit_agent.supervisor import run_supervisor
from livekit_agent.turn_control import TurnCoordinator

if TYPE_CHECKING:
    from livekit.agents import AgentSession


def _uses_controlled_speech() -> bool:
    return config.SUPERVISOR_ENABLED and config.SUPERVISOR_MODE == "controlled"


async def _end_on_llm_failure(
    *,
    session_id: str,
    turn_id: str,
    state: ConsultationState,
    session: AgentSession | None,
    pipeline_started: float,
    reason: str,
    phase: str = "supervisor",
) -> None:
    """Speak once, mark consultation ended, notify UI — do not invite another turn."""
    state.phase = "ended"
    spoken = config.LLM_FATAL_UTTERANCE
    emit_pipeline_event(
        session_id=session_id,
        turn_id=turn_id,
        phase=phase,
        status="error",
        message=f"LLM failure: {reason}",
        data={"error": reason, "fatal": True},
        elapsed_ms=int((time.monotonic() - pipeline_started) * 1000),
    )
    log_event(
        "SUP",
        "llm_fatal",
        session_id=session_id,
        turn_id=turn_id,
        detail=f"reason={reason}",
    )
    if _uses_controlled_speech() and session is not None:
        try:
            await session.generate_reply(
                instructions=f"Say exactly: {spoken}",
                tool_choice="none",
            )
        except Exception as exc:
            log_event(
                "VOICE",
                "speech_error",
                session_id=session_id,
                turn_id=turn_id,
                detail=f"fatal_utterance_failed {exc}",
            )
    emit_pipeline_event(
        session_id=session_id,
        turn_id=turn_id,
        phase="session",
        status="error",
        message="Consultation ended due to a technical problem",
        data={"fatal": True, "reason": reason, "user_message": spoken},
        elapsed_ms=int((time.monotonic() - pipeline_started) * 1000),
    )
    emit_pipeline_event(
        session_id=session_id,
        turn_id=turn_id,
        phase="turn",
        status="error",
        message="Consultation pipeline ended after LLM failure",
        data={"fatal": True, "reason": reason},
        elapsed_ms=int((time.monotonic() - pipeline_started) * 1000),
    )


async def handle_patient_turn(
    session_id: str,
    turn_id: str,
    patient_text: str,
    state: ConsultationState,
    session: AgentSession | None = None,
    coordinator: TurnCoordinator | None = None,
) -> None:
    """Part 3: supervisor decides; controlled mode speaks approved content only."""
    if not config.SUPERVISOR_ENABLED:
        return
    if state.phase == "ended":
        log_event(
            "SUP",
            "turn_ignored",
            session_id=session_id,
            turn_id=turn_id,
            detail="phase=ended",
        )
        return

    pipeline_started = time.monotonic()
    emit_pipeline_event(
        session_id=session_id,
        turn_id=turn_id,
        phase="turn",
        status="started",
        message="Patient turn received — starting consultation pipeline",
        data={
            "patient_text_chars": len(patient_text),
            "patient_text": patient_text[:800],
        },
    )

    log_event(
        "SUP",
        "supervisor_started",
        session_id=session_id,
        turn_id=turn_id,
        detail=f"mode={config.SUPERVISOR_MODE}",
    )
    started = time.monotonic()

    snap = state.snapshot()
    assessment_evidence = None
    if config.ASSESSMENT_RAG_ENABLED:
        emit_pipeline_event(
            session_id=session_id,
            turn_id=turn_id,
            phase="assessment_rag",
            status="started",
            message="Searching assessment question index",
            data={"source": "medquad_assessment"},
        )
        log_event(
            "RAG",
            "retrieval_started",
            session_id=session_id,
            turn_id=turn_id,
            detail="source=medquad_assessment",
        )
        # Sync Qdrant/HF must not block the LiveKit audio loop.
        assessment_evidence = await asyncio.to_thread(
            assessment_search,
            chief_complaint=snap.get("chief_complaint"),
            known_facts=snap.get("facts") or {},
            already_asked=snap.get("asked_topics") or [],
            patient_turn=patient_text,
        )
        assessment_msg, assessment_data = assessment_completed_event(assessment_evidence)
        emit_pipeline_event(
            session_id=session_id,
            turn_id=turn_id,
            phase="assessment_rag",
            status="completed",
            message=assessment_msg,
            data=assessment_data,
            elapsed_ms=int((time.monotonic() - started) * 1000),
        )
        log_event(
            "RAG",
            "retrieval_finished",
            session_id=session_id,
            turn_id=turn_id,
            detail=(
                f"source={assessment_evidence.get('source')} "
                f"pack={assessment_evidence.get('pack')} "
                f"suggestions={len(assessment_evidence.get('suggested_questions') or [])}"
            ),
        )

    emit_pipeline_event(
        session_id=session_id,
        turn_id=turn_id,
        phase="supervisor",
        status="started",
        message="Supervisor analyzing patient turn",
        data={"phase": snap.get("phase"), "followup_count": snap.get("followup_count")},
    )

    try:
        decision = await asyncio.wait_for(
            run_supervisor(
                patient_turn=patient_text,
                state=snap,
                session_id=session_id,
                turn_id=turn_id,
                assessment_evidence=assessment_evidence,
            ),
            timeout=config.SUPERVISOR_TIMEOUT_SEC,
        )
    except asyncio.TimeoutError:
        await _end_on_llm_failure(
            session_id=session_id,
            turn_id=turn_id,
            state=state,
            session=session,
            pipeline_started=pipeline_started,
            reason="supervisor_timeout",
            phase="supervisor",
        )
        return
    except asyncio.CancelledError:
        emit_pipeline_event(
            session_id=session_id,
            turn_id=turn_id,
            phase="turn",
            status="error",
            message="Consultation pipeline cancelled",
            elapsed_ms=int((time.monotonic() - pipeline_started) * 1000),
        )
        raise
    except Exception as exc:
        log_event(
            "SUP",
            "supervisor_error",
            session_id=session_id,
            turn_id=turn_id,
            detail=f"+{int((time.monotonic() - started) * 1000)}ms {exc}",
        )
        await _end_on_llm_failure(
            session_id=session_id,
            turn_id=turn_id,
            state=state,
            session=session,
            pipeline_started=pipeline_started,
            reason=f"supervisor_error:{exc}",
            phase="supervisor",
        )
        return

    elapsed_ms = int((time.monotonic() - started) * 1000)
    emit_pipeline_event(
        session_id=session_id,
        turn_id=turn_id,
        phase="supervisor",
        status="completed",
        message=f"Supervisor chose action: {decision.action}",
        data={
            "action": decision.action,
            "confidence": decision.confidence,
            "followup_topic": decision.followup_topic,
            "reason": decision.reason,
            "spoken_utterance": (decision.spoken_utterance or "")[:800],
        },
        elapsed_ms=elapsed_ms,
    )
    log_event(
        "SUP",
        "decision",
        session_id=session_id,
        turn_id=turn_id,
        detail=(
            f"+{elapsed_ms}ms action={decision.action} "
            f"confidence={decision.confidence:.2f}"
        ),
    )

    result = validate_and_apply(state, decision)
    validated_ms = int((time.monotonic() - started) * 1000)
    if result.ok:
        log_event(
            "CTRL",
            "decision_validated",
            session_id=session_id,
            turn_id=turn_id,
            detail=f"+{validated_ms}ms ok=true",
        )
        log_event(
            "CTRL",
            "state_committed",
            session_id=session_id,
            turn_id=turn_id,
            detail=f"phase={state.phase} followups={state.followup_count}",
        )
        emit_pipeline_event(
            session_id=session_id,
            turn_id=turn_id,
            phase="state",
            status="completed",
            message="Consultation state updated",
            data={
                "phase": state.phase,
                "followup_count": state.followup_count,
                "chief_complaint": state.chief_complaint,
            },
            elapsed_ms=validated_ms,
        )
    else:
        emit_pipeline_event(
            session_id=session_id,
            turn_id=turn_id,
            phase="state",
            status="error",
            message="Supervisor decision rejected",
            data={"error": result.error},
            elapsed_ms=validated_ms,
        )
        log_event(
            "CTRL",
            "decision_validated",
            session_id=session_id,
            turn_id=turn_id,
            detail=f"+{validated_ms}ms ok=false error={result.error}",
        )
        emit_pipeline_event(
            session_id=session_id,
            turn_id=turn_id,
            phase="turn",
            status="error",
            message="Consultation pipeline stopped at validation",
            elapsed_ms=int((time.monotonic() - pipeline_started) * 1000),
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

    guidance_result = None
    if decision.action == "build_final_query":
        package = build_case_package(state)
        emit_pipeline_event(
            session_id=session_id,
            turn_id=turn_id,
            phase="case_package",
            status="completed",
            message="Final case package ready for knowledge retrieval",
            data={
                "ready_for_retrieval": package.get("ready_for_retrieval"),
                "final_query_chars": len(package.get("final_query") or ""),
                "phase": package.get("phase"),
            },
        )
        log_event(
            "CTRL",
            "case_package_ready",
            session_id=session_id,
            turn_id=turn_id,
            detail=(
                f"ready_for_retrieval={package.get('ready_for_retrieval')} "
                f"query_chars={len(package.get('final_query') or '')}"
            ),
        )
        log_note(
            session_id,
            "\n".join(
                [
                    f"CASE PACKAGE ({turn_id}):",
                    json.dumps(package, ensure_ascii=False, indent=2),
                ]
            ),
        )
        if package.get("ready_for_retrieval"):
            guidance_result = await run_knowledge_guidance(
                package,
                session_id=session_id,
                turn_id=turn_id,
            )
            if guidance_result is not None:
                if guidance_result.get("error") and not (
                    guidance_result.get("spoken_answer")
                    or (guidance_result.get("guidance") or {}).get("spoken_answer")
                ):
                    await _end_on_llm_failure(
                        session_id=session_id,
                        turn_id=turn_id,
                        state=state,
                        session=session,
                        pipeline_started=pipeline_started,
                        reason=f"guidance_error:{guidance_result.get('error')}",
                        phase="guidance",
                    )
                    return
                log_note(
                    session_id,
                    "\n".join(
                        [
                            f"KNOWLEDGE GUIDANCE ({turn_id}):",
                            json.dumps(guidance_result, ensure_ascii=False, indent=2),
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
        emit_pipeline_event(
            session_id=session_id,
            turn_id=turn_id,
            phase="turn",
            status="completed",
            message="Pipeline finished (speech deferred — log_only mode)",
            elapsed_ms=int((time.monotonic() - pipeline_started) * 1000),
        )
        return

    if session is None:
        log_event(
            "VOICE",
            "speech_error",
            session_id=session_id,
            turn_id=turn_id,
            detail="no session for controlled speech",
        )
        emit_pipeline_event(
            session_id=session_id,
            turn_id=turn_id,
            phase="speech",
            status="error",
            message="No voice session available for response",
        )
        emit_pipeline_event(
            session_id=session_id,
            turn_id=turn_id,
            phase="turn",
            status="error",
            message="Consultation pipeline finished without speech",
            elapsed_ms=int((time.monotonic() - pipeline_started) * 1000),
        )
        return

    speech_source = (
        "knowledge_guidance"
        if guidance_result and guidance_result.get("spoken_answer")
        else "supervisor"
    )
    emit_pipeline_event(
        session_id=session_id,
        turn_id=turn_id,
        phase="speech",
        status="started",
        message="Preparing voice response",
        data={"source": speech_source},
    )
    log_event(
        "VOICE",
        "speech_requested",
        session_id=session_id,
        turn_id=turn_id,
        detail=(
            f"paraphrase={decision.allow_light_paraphrase} source={speech_source}"
        ),
    )
    speech_started = time.monotonic()
    try:
        guidance_payload = guidance_result.get("guidance") or guidance_result if guidance_result else {}
        if guidance_payload.get("spoken_answer"):
            await speak_guidance(session, guidance_payload)
        else:
            await speak_decision(session, decision)
    except Exception as exc:
        emit_pipeline_event(
            session_id=session_id,
            turn_id=turn_id,
            phase="speech",
            status="error",
            message="Voice response failed",
            data={"error": str(exc)},
        )
        log_event(
            "VOICE",
            "speech_error",
            session_id=session_id,
            turn_id=turn_id,
            detail=str(exc),
        )
        emit_pipeline_event(
            session_id=session_id,
            turn_id=turn_id,
            phase="turn",
            status="error",
            message="Consultation pipeline failed at speech",
            elapsed_ms=int((time.monotonic() - pipeline_started) * 1000),
        )
        return

    speech_ms = int((time.monotonic() - speech_started) * 1000)
    emit_pipeline_event(
        session_id=session_id,
        turn_id=turn_id,
        phase="speech",
        status="completed",
        message="Voice response delivered",
        data={"source": speech_source},
        elapsed_ms=speech_ms,
    )
    log_event(
        "VOICE",
        "speech_done",
        session_id=session_id,
        turn_id=turn_id,
        detail=f"elapsed_ms={speech_ms}",
    )
    emit_pipeline_event(
        session_id=session_id,
        turn_id=turn_id,
        phase="turn",
        status="completed",
        message="Consultation pipeline finished",
        data={"action": decision.action, "speech_source": speech_source},
        elapsed_ms=int((time.monotonic() - pipeline_started) * 1000),
    )
