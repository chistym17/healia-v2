"""Question templates and conversational rewrites for assessment retrieval."""

from __future__ import annotations

import re

# Expanded per-topic question types (index build).
QUESTION_TEMPLATES: list[tuple[str, str]] = [
    ("symptoms", "What are the symptoms of {topic}?"),
    ("causes", "What causes {topic}?"),
    ("diagnosis", "How is {topic} diagnosed?"),
    ("treatment", "How is {topic} treated?"),
    ("risk", "Who is at risk for {topic}?"),
    ("prevention", "How can {topic} be prevented?"),
    ("definition", "What is {topic}?"),
]

# Prefer clinical follow-up types over definitions at retrieval time.
TYPE_PRIORITY: list[str] = [
    "symptoms",
    "causes",
    "diagnosis",
    "treatment",
    "risk",
    "prevention",
    "definition",
    "general",
]

_TYPE_RANK = {t: i for i, t in enumerate(TYPE_PRIORITY)}

# Short theme labels for the supervisor (not spoken scripts).
TYPE_THEMES: dict[str, str] = {
    "symptoms": "associated_symptoms",
    "causes": "onset_or_triggers",
    "diagnosis": "prior_evaluation",
    "treatment": "self_care_or_medicines",
    "risk": "related_history",
    "prevention": "aggravating_relieving",
    "definition": "character_of_complaint",
    "general": "more_detail",
}


def type_rank(question_type: str) -> int:
    return _TYPE_RANK.get(question_type, len(TYPE_PRIORITY))


def _clean_phrase(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).lower()[:80]


def resolve_focus(
    *,
    medical_topic: str = "",
    chief_complaint: str | None = None,
    patient_turn: str = "",
) -> str:
    """Prefer the patient's own complaint wording over a retrieved topic label."""
    for candidate in (chief_complaint, patient_turn, medical_topic):
        cleaned = _clean_phrase(str(candidate or ""))
        if cleaned and len(cleaned) > 2:
            # Prefer short symptom phrases over long sentences.
            if candidate is patient_turn and len(cleaned) > 48:
                continue
            return cleaned
    return ""


def to_conversational(
    question_type: str,
    medical_topic: str,
    *,
    chief_complaint: str | None = None,
    patient_turn: str = "",
) -> str:
    """Build a short hint question grounded in this patient's focus phrase."""
    focus = resolve_focus(
        medical_topic=medical_topic,
        chief_complaint=chief_complaint,
        patient_turn=patient_turn,
    )
    qtype = (question_type or "general").strip().lower()

    if not focus:
        return {
            "symptoms": "What other symptoms are you noticing with this?",
            "causes": "Did anything seem to start this or make it worse?",
            "diagnosis": "Have you had this checked before?",
            "treatment": "Have you taken anything so far for this?",
            "risk": "Is there any related medical history I should know?",
            "prevention": "Has anything helped or made this worse?",
            "definition": "Can you describe what this has been like?",
            "general": "Can you tell me a bit more about what is going on?",
        }.get(qtype, "Can you tell me a bit more about what is going on?")

    if qtype == "symptoms":
        return f"Along with your {focus}, what other symptoms are you noticing?"
    if qtype == "causes":
        return f"For this {focus}, did it start suddenly or build gradually?"
    if qtype == "diagnosis":
        return f"Have you had anything like this {focus} evaluated before?"
    if qtype == "treatment":
        return f"Have you tried anything yet for your {focus}?"
    if qtype == "risk":
        return f"Have you had similar {focus} problems before?"
    if qtype == "prevention":
        return f"Does anything make your {focus} better or worse?"
    if qtype == "definition":
        return f"Can you describe your {focus} more — where it is and how strong it feels?"
    return f"What else stands out about your {focus} right now?"


QUESTION_TYPE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("symptoms", re.compile(r"symptom", re.I)),
    ("causes", re.compile(r"what cause|causes of|why do", re.I)),
    ("diagnosis", re.compile(r"diagnos|test|screen", re.I)),
    ("treatment", re.compile(r"treat|therapy|manage|medicine|drug", re.I)),
    ("risk", re.compile(r"at risk|risk factor|who gets", re.I)),
    ("prevention", re.compile(r"prevent|avoid", re.I)),
    ("definition", re.compile(r"what is|what are", re.I)),
]


def infer_question_type_from_text(question: str) -> str:
    for label, pattern in QUESTION_TYPE_PATTERNS:
        if pattern.search(question):
            return label
    return "general"
