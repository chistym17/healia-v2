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


def type_rank(question_type: str) -> int:
    return _TYPE_RANK.get(question_type, len(TYPE_PRIORITY))


# Supervisor-facing phrasing (voice-friendly).
CONVERSATIONAL: dict[str, str] = {
    "symptoms": "What other symptoms have you noticed?",
    "causes": "Did anything seem to trigger this or make it start?",
    "diagnosis": "Have you had any tests or seen a doctor for this before?",
    "treatment": "Are you taking any medications or treatments for this?",
    "risk": "Do you have any medical conditions that might relate to this?",
    "prevention": "Have you tried anything that helps or makes it worse?",
    "definition": "Can you describe what you've been experiencing?",
    "general": "Can you tell me a bit more about what is going on?",
}


def to_conversational(question_type: str, medical_topic: str) -> str:
    """Turn a retrieved type + topic into a natural assessment question."""
    base = CONVERSATIONAL.get(question_type, CONVERSATIONAL["general"])
    topic_lower = medical_topic.lower()
    # Light topic grounding when the template is generic.
    if question_type == "symptoms" and medical_topic:
        return f"Besides what you mentioned, have you had other symptoms related to {topic_lower}?"
    if question_type == "definition" and medical_topic:
        return f"Can you describe what your {topic_lower} has been like?"
    return base


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
