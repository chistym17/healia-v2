"""Part 5: final query / case package handoff + knowledge guidance hook."""

from __future__ import annotations

from typing import Any

from livekit_agent.state import ConsultationState


def has_patient_substance(state: ConsultationState) -> bool:
    """True when the consultation collected something usable for guidance."""
    if (state.chief_complaint or "").strip():
        return True
    if any(str(v).strip() for v in state.facts.values()):
        return True
    if (state.final_query_draft or "").strip():
        return True
    return False


def build_case_package(state: ConsultationState) -> dict[str, Any]:
    """Structured case summary ready for future guidance retrieval."""
    draft = (state.final_query_draft or "").strip()
    substance = has_patient_substance(state)
    return {
        "session_id": state.session_id,
        "final_query": state.final_query_draft,
        "chief_complaint": state.chief_complaint,
        "facts": dict(state.facts),
        "asked_topics": list(state.asked_topics),
        "phase": state.phase,
        "followup_count": state.followup_count,
        "has_patient_substance": substance,
        "ready_for_retrieval": bool(draft)
        and substance
        and state.phase in ("ready", "ended"),
    }


def draft_final_query_from_state(state: ConsultationState) -> str:
    """Best-effort final query when the user ends early but shared symptoms."""
    if (state.final_query_draft or "").strip():
        return state.final_query_draft.strip()
    parts: list[str] = []
    if (state.chief_complaint or "").strip():
        parts.append(state.chief_complaint.strip())
    for key, value in state.facts.items():
        text = str(value).strip()
        if text:
            parts.append(f"{key}: {text}")
    return ". ".join(parts)
