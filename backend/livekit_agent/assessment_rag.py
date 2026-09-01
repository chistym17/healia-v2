"""Assessment retrieval: MedQuAD question index with mock fallback."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_MOCKS_DIR = Path(__file__).resolve().parent / "mocks"
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

_PACK_ALIASES = {
    "headache": "headache",
    "migraine": "headache",
    "head pain": "headache",
}


def _load_pack(name: str) -> dict[str, Any]:
    path = _MOCKS_DIR / f"{name}.json"
    if not path.is_file():
        path = _MOCKS_DIR / "default.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _pick_pack_name(chief_complaint: str | None, patient_turn: str = "") -> str:
    text = f"{chief_complaint or ''} {patient_turn}".lower()
    for needle, pack in _PACK_ALIASES.items():
        if needle in text:
            return pack
    return "default"


def _mock_search(
    *,
    chief_complaint: str | None,
    known_facts: dict[str, Any] | None,
    already_asked: list[str] | None,
    patient_turn: str = "",
) -> dict[str, Any]:
    asked = {t.strip() for t in (already_asked or []) if t and str(t).strip()}
    pack_name = _pick_pack_name(chief_complaint, patient_turn)
    pack = _load_pack(pack_name)

    suggested = []
    for item in pack.get("suggested_questions") or []:
        topic = str(item.get("topic") or "").strip()
        if not topic or topic in asked:
            continue
        suggested.append(
            {
                "topic": topic,
                "question": str(item.get("question") or "").strip(),
            }
        )

    return {
        "source": "mock",
        "pack": pack_name,
        "red_flag_hints": list(pack.get("red_flag_hints") or []),
        "suggested_questions": suggested,
        "known_fact_keys": list((known_facts or {}).keys()),
        "already_asked": list(asked),
    }


def search(
    *,
    chief_complaint: str | None,
    known_facts: dict[str, Any] | None,
    already_asked: list[str] | None,
    patient_turn: str = "",
) -> dict[str, Any]:
    """Return assessment hints from MedQuAD index, or mock if index unavailable."""
    try:
        from medical_rag.assessment.search import search_questions

        return search_questions(
            chief_complaint=chief_complaint,
            known_facts=known_facts,
            already_asked=already_asked,
            patient_turn=patient_turn,
        )
    except Exception:
        return _mock_search(
            chief_complaint=chief_complaint,
            known_facts=known_facts,
            already_asked=already_asked,
            patient_turn=patient_turn,
        )
