"""Light dialogue guardrails (not the consultation brain).

Supervisor LLM decides medical understanding. These helpers only:
- skip assessment RAG on empty/greeting turns
- detect clear denials of the current chief complaint
- block follow-ups that still mention denied complaints
"""

from __future__ import annotations

import re
from typing import Any

_GREETING_ONLY = re.compile(
    r"^\s*("
    r"hi|hello|hey|hiya|yo|"
    r"good\s*(morning|afternoon|evening)|"
    r"howdy|thanks|thank\s*you|ok|okay|yes|no|yeah|yep|nah|"
    r"please|help|start|begin"
    r")[\s!.?]*$",
    re.IGNORECASE,
)

_DENIAL_CUES = (
    "not having",
    "don't have",
    "do not have",
    "i don't have",
    "i do not have",
    "i'm not having",
    "i am not having",
    "never had",
    "not my",
    "wrong",
    "incorrect",
    "that's not",
    "that is not",
)


def looks_like_non_medical_opener(text: str) -> bool:
    """True for greetings / fillers with no usable medical content."""
    t = (text or "").strip()
    if not t:
        return True
    if len(t) <= 2:
        return True
    if _GREETING_ONLY.match(t):
        return True
    # Very short social openers
    words = re.findall(r"[a-zA-Z']+", t.lower())
    if len(words) <= 2 and words and words[0] in {
        "hi", "hello", "hey", "thanks", "ok", "okay", "yes", "no",
    }:
        return True
    return False


def should_run_assessment_rag(
    *,
    chief_complaint: str | None,
    patient_turn: str,
) -> bool:
    """Only retrieve question themes when we have a real complaint signal."""
    if (chief_complaint or "").strip():
        return True
    if looks_like_non_medical_opener(patient_turn):
        return False
    # First symptom-like turn with no complaint yet — allow retrieval from the turn.
    words = re.findall(r"[a-zA-Z']+", (patient_turn or "").lower())
    return len(words) >= 3


_VAGUE_DENIALS = (
    "not having that",
    "don't have that",
    "do not have that",
    "that's wrong",
    "that is wrong",
    "that's not right",
    "what are you talking about",
    "wrong symptom",
)


def detect_denied_complaints(
    patient_turn: str,
    chief_complaint: str | None,
) -> list[str]:
    """
    If the patient clearly denies the current chief complaint, return it.
    Used only as a sticky-state safety net — not for inventing new diagnoses.
    """
    complaint = (chief_complaint or "").strip()
    if not complaint:
        return []
    text = (patient_turn or "").strip().lower()
    if not text:
        return []

    complaint_l = complaint.lower()
    tokens = [t for t in re.findall(r"[a-zA-Z']+", complaint_l) if len(t) > 2]
    names_complaint = complaint_l in text or (
        bool(tokens) and all(tok in text for tok in tokens)
    )
    has_denial_cue = any(cue in text for cue in _DENIAL_CUES)
    vague_denial = any(p in text for p in _VAGUE_DENIALS)

    if names_complaint and has_denial_cue:
        return [complaint]
    if vague_denial:
        return [complaint]
    return []


def utterance_mentions_denied(spoken: str, denied: list[str]) -> bool:
    text = (spoken or "").lower()
    if not text or not denied:
        return False
    for item in denied:
        term = (item or "").strip().lower()
        if not term:
            continue
        if term in text:
            return True
        tokens = [t for t in re.findall(r"[a-zA-Z']+", term) if len(t) > 3]
        if tokens and all(tok in text for tok in tokens):
            return True
    return False


def filter_assessment_evidence(
    evidence: dict[str, Any] | None,
    denied: list[str],
) -> dict[str, Any] | None:
    """Drop suggestion rows that still center a denied complaint."""
    if not evidence or not denied:
        return evidence
    suggestions = evidence.get("suggested_questions") or []
    kept = []
    for item in suggestions:
        blob = " ".join(
            str(item.get(k) or "")
            for k in ("topic", "theme", "medical_topic", "question", "question_type")
        )
        if utterance_mentions_denied(blob, denied):
            continue
        kept.append(item)
    out = dict(evidence)
    out["suggested_questions"] = kept
    out["denied_filtered"] = len(suggestions) - len(kept)
    return out


def empty_assessment_evidence(*, reason: str) -> dict[str, Any]:
    return {
        "source": "skipped",
        "pack": None,
        "red_flag_hints": [],
        "suggested_questions": [],
        "known_fact_keys": [],
        "already_asked": [],
        "skip_reason": reason,
    }
