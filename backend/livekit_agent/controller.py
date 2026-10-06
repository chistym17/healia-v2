from __future__ import annotations

from dataclasses import dataclass

from livekit_agent import config
from livekit_agent.dialogue_guards import utterance_mentions_denied
from livekit_agent.state import ConsultationState
from livekit_agent.supervisor import SupervisorDecision


@dataclass
class ValidationResult:
    ok: bool
    error: str = ""
    decision: SupervisorDecision | None = None


def validate_and_apply(
    state: ConsultationState,
    decision: SupervisorDecision,
) -> ValidationResult:
    if not decision.spoken_utterance and decision.action not in ("end",):
        return ValidationResult(
            ok=False,
            error="missing spoken_utterance",
            decision=decision,
        )

    updates = decision.state_updates if isinstance(decision.state_updates, dict) else {}
    deny_complaints = updates.get("deny_complaints") or []
    if not isinstance(deny_complaints, list):
        deny_complaints = []
    denied_after = list(state.denied_complaints)
    for item in deny_complaints:
        text = str(item or "").strip()
        if text and not any(d.lower() == text.lower() for d in denied_after):
            denied_after.append(text)

    if decision.action == "ask_followup":
        topic = decision.followup_topic
        if not topic:
            return ValidationResult(
                ok=False,
                error="ask_followup requires followup_topic",
                decision=decision,
            )
        if topic in state.asked_topics:
            return ValidationResult(
                ok=False,
                error=f"duplicate followup_topic={topic}",
                decision=decision,
            )
        if state.followup_count >= config.SUPERVISOR_MAX_FOLLOWUPS:
            return ValidationResult(
                ok=False,
                error="followup cap reached",
                decision=decision,
            )
        if utterance_mentions_denied(decision.spoken_utterance, denied_after):
            return ValidationResult(
                ok=False,
                error="followup mentions denied complaint",
                decision=decision,
            )

    if decision.action == "build_final_query":
        draft = updates.get("final_query_draft") or state.final_query_draft
        if not draft:
            return ValidationResult(
                ok=False,
                error="build_final_query requires final_query_draft",
                decision=decision,
            )

    clear_chief = bool(updates.get("clear_chief_complaint"))
    chief_update = updates.get("chief_complaint")
    # Allow explicit null/"" clear via chief_complaint field.
    if chief_update is not None and not str(chief_update).strip():
        clear_chief = True
        chief_update = None

    state.apply_updates(
        new_facts=updates.get("new_facts"),
        corrections=updates.get("corrections"),
        chief_complaint=None if clear_chief and chief_update is None else (
            str(chief_update) if chief_update is not None else None
        ),
        clear_chief_complaint=clear_chief,
        deny_complaints=[str(x) for x in deny_complaints],
        final_query_draft=updates.get("final_query_draft"),
        phase=updates.get("phase"),
        add_asked_topics=updates.get("add_asked_topics"),
    )

    # If clear was requested without a replacement, ensure complaint is gone.
    if clear_chief and chief_update is None:
        state.chief_complaint = None

    if decision.action == "ask_followup" and decision.followup_topic:
        state.apply_updates(add_asked_topics=[decision.followup_topic])
        state.followup_count += 1

    if decision.action == "build_final_query":
        draft = updates.get("final_query_draft")
        if draft:
            state.final_query_draft = str(draft)
        state.phase = "ready"

    if decision.action == "escalate":
        state.phase = "escalated"

    if decision.action == "end":
        state.phase = "ended"

    return ValidationResult(ok=True, decision=decision)
