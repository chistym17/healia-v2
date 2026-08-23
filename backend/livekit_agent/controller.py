from __future__ import annotations

from dataclasses import dataclass

from livekit_agent import config
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

    if decision.action == "build_final_query":
        draft = decision.state_updates.get("final_query_draft") or state.final_query_draft
        if not draft:
            return ValidationResult(
                ok=False,
                error="build_final_query requires final_query_draft",
                decision=decision,
            )

    updates = decision.state_updates
    state.apply_updates(
        new_facts=updates.get("new_facts"),
        corrections=updates.get("corrections"),
        chief_complaint=updates.get("chief_complaint"),
        final_query_draft=updates.get("final_query_draft"),
        phase=updates.get("phase"),
        add_asked_topics=updates.get("add_asked_topics"),
    )

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
