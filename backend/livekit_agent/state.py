from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConsultationState:
    """Mutable consultation state committed only after Python validation."""

    session_id: str
    chief_complaint: str | None = None
    facts: dict[str, Any] = field(default_factory=dict)
    asked_topics: list[str] = field(default_factory=list)
    phase: str = "gathering"
    final_query_draft: str | None = None
    followup_count: int = 0

    def snapshot(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "chief_complaint": self.chief_complaint,
            "facts": dict(self.facts),
            "asked_topics": list(self.asked_topics),
            "phase": self.phase,
            "final_query_draft": self.final_query_draft,
            "followup_count": self.followup_count,
        }

    def apply_updates(
        self,
        *,
        new_facts: dict[str, Any] | None = None,
        corrections: dict[str, Any] | None = None,
        chief_complaint: str | None = None,
        final_query_draft: str | None = None,
        phase: str | None = None,
        add_asked_topics: list[str] | None = None,
    ) -> None:
        if chief_complaint:
            self.chief_complaint = chief_complaint
        for key, value in (new_facts or {}).items():
            if value is not None and value != "":
                self.facts[key] = value
        for key, value in (corrections or {}).items():
            if value is not None and value != "":
                self.facts[key] = value
        if final_query_draft:
            self.final_query_draft = final_query_draft
        if phase:
            self.phase = phase
        for topic in add_asked_topics or []:
            topic = (topic or "").strip()
            if topic and topic not in self.asked_topics:
                self.asked_topics.append(topic)
