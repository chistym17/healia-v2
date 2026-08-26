"""Part 5: final query / case package handoff (pre–full guidance RAG)."""

from __future__ import annotations

from typing import Any

from livekit_agent.state import ConsultationState


def build_case_package(state: ConsultationState) -> dict[str, Any]:
    """Structured case summary ready for future guidance retrieval."""
    return {
        "session_id": state.session_id,
        "final_query": state.final_query_draft,
        "chief_complaint": state.chief_complaint,
        "facts": dict(state.facts),
        "asked_topics": list(state.asked_topics),
        "phase": state.phase,
        "followup_count": state.followup_count,
        "ready_for_retrieval": bool(state.final_query_draft)
        and state.phase in ("ready", "ended"),
    }
