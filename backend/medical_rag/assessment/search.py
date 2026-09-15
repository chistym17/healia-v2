"""Search the MedQuAD assessment question index (small FAISS store)."""

from __future__ import annotations

import json
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import faiss
import numpy as np
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from questions import TYPE_PRIORITY, TYPE_THEMES, to_conversational, type_rank

STORE_DIR = ROOT / "store"
CONFIG_PATH = ROOT / "config.json"

DEFAULT_TOP_K = 30
MAX_SUGGESTIONS = 5

GENERIC_RED_FLAGS = [
    "Severe or rapidly worsening symptoms",
    "Difficulty breathing",
    "Chest pain",
    "Confusion or fainting",
]


def _load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_endpoint(cfg: dict) -> str:
    load_dotenv(ROOT.parent.parent / ".env")
    emb = cfg["embedding"]
    return os.getenv(emb["endpoint_env"]) or emb["default_endpoint"]


def _truncate(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars]


def _l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-12)
    return (vectors / norms).astype(np.float32)


def build_query(
    chief_complaint: str | None,
    known_facts: dict[str, Any] | None,
    patient_turn: str = "",
) -> str:
    parts: list[str] = []
    if chief_complaint and str(chief_complaint).strip():
        parts.append(str(chief_complaint).strip())
    if patient_turn and str(patient_turn).strip():
        parts.append(str(patient_turn).strip())
    for value in (known_facts or {}).values():
        if value is None:
            continue
        text = str(value).strip()
        if text:
            parts.append(text)
    return " ".join(parts).strip()


def _topic_key(meta: dict[str, Any]) -> str:
    qtype = (meta.get("question_type") or "general").strip()
    topic = (meta.get("topic") or "").strip()
    if topic and qtype:
        return f"{topic.lower()}:{qtype}"
    return qtype or topic.lower() or "general"


def _clear_index_cache() -> None:
    _load_index.cache_clear()


@lru_cache(maxsize=1)
def _load_index() -> tuple[faiss.Index, list[dict[str, Any]], dict]:
    index_path = STORE_DIR / "index.faiss"
    metadata_path = STORE_DIR / "metadata.jsonl"
    if not index_path.is_file() or not metadata_path.is_file():
        raise FileNotFoundError(
            f"Assessment index missing under {STORE_DIR}. "
            "Run: python medical_rag/assessment/build_index.py"
        )

    cfg = _load_config()
    metadata = [
        json.loads(line)
        for line in metadata_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    index = faiss.read_index(str(index_path))
    if index.ntotal != len(metadata):
        raise RuntimeError(
            f"Assessment index rows={index.ntotal} != metadata={len(metadata)}"
        )
    return index, metadata, cfg


def _embed_query(query: str, cfg: dict, endpoint: str) -> np.ndarray:
    emb = cfg["embedding"]
    payload = {
        "inputs": [_truncate(query, int(emb.get("truncate_chars", 900)))]
    }
    resp = requests.post(
        endpoint,
        json=payload,
        timeout=int(emb.get("request_timeout_sec", 60)),
    )
    resp.raise_for_status()
    return _l2_normalize(np.asarray(resp.json(), dtype=np.float32))


def _diversify_hits(
    hits: list[dict[str, Any]],
    *,
    max_suggestions: int,
    asked: set[str],
) -> list[dict[str, Any]]:
    """Pick varied question types; prefer anchor topic from top hit."""
    if not hits:
        return []

    anchor_topic = hits[0]["medical_topic"].lower()
    used_types: set[str] = set()
    used_keys: set[str] = set()
    selected: list[dict[str, Any]] = []

    def try_add(hit: dict[str, Any]) -> bool:
        qtype = hit["question_type"]
        topic_key = hit["topic"].lower()
        medical_lower = hit["medical_topic"].lower()
        if topic_key in asked or medical_lower in asked:
            return False
        if qtype in used_types or topic_key in used_keys:
            return False
        used_types.add(qtype)
        used_keys.add(topic_key)
        selected.append(hit)
        return True

    # Pass 1: anchor topic, clinical types first.
    anchor_hits = sorted(
        [h for h in hits if h["medical_topic"].lower() == anchor_topic],
        key=lambda h: (type_rank(h["question_type"]), -h["score"]),
    )
    for hit in anchor_hits:
        if len(selected) >= max_suggestions:
            break
        try_add(hit)

    # Pass 2: other topics, still diversify by type.
    other_hits = sorted(
        [h for h in hits if h["medical_topic"].lower() != anchor_topic],
        key=lambda h: (type_rank(h["question_type"]), -h["score"]),
    )
    for hit in other_hits:
        if len(selected) >= max_suggestions:
            break
        try_add(hit)

    # Pass 3: fill any remaining slots (allow second topic if needed).
    if len(selected) < max_suggestions:
        for hit in sorted(hits, key=lambda h: (type_rank(h["question_type"]), -h["score"])):
            if len(selected) >= max_suggestions:
                break
            topic_key = hit["topic"].lower()
            if topic_key in asked or topic_key in used_keys:
                continue
            used_keys.add(topic_key)
            selected.append(hit)

    return selected


def search_questions(
    *,
    chief_complaint: str | None,
    known_facts: dict[str, Any] | None,
    already_asked: list[str] | None,
    patient_turn: str = "",
    top_k: int = DEFAULT_TOP_K,
    max_suggestions: int = MAX_SUGGESTIONS,
) -> dict[str, Any]:
    """Retrieve MedQuAD question candidates for assessment."""
    asked = {t.strip().lower() for t in (already_asked or []) if t and str(t).strip()}
    query = build_query(chief_complaint, known_facts, patient_turn)
    if not query:
        return {
            "source": "medquad_assessment",
            "pack": "empty_query",
            "red_flag_hints": GENERIC_RED_FLAGS,
            "suggested_questions": [],
            "known_fact_keys": list((known_facts or {}).keys()),
            "already_asked": list(asked),
            "query": query,
        }

    index, metadata, cfg = _load_index()
    endpoint = _resolve_endpoint(cfg)
    qvec = _embed_query(query, cfg, endpoint)
    scores, indices = index.search(qvec, top_k)

    raw_hits: list[dict[str, Any]] = []
    for idx, score in zip(indices[0], scores[0]):
        if idx < 0:
            continue
        row = metadata[int(idx)]
        meta = row.get("metadata") or {}
        medical_topic = (row.get("topic") or meta.get("topic") or "").strip()
        canonical = (row.get("question") or meta.get("question") or "").strip()
        qtype = str(meta.get("question_type") or "general")
        if not canonical:
            continue
        raw_hits.append(
            {
                "topic": _topic_key(meta),
                "canonical_question": canonical,
                "question": to_conversational(
                    qtype,
                    medical_topic,
                    chief_complaint=chief_complaint,
                    patient_turn=patient_turn,
                ),
                "medical_topic": medical_topic,
                "question_type": qtype,
                "theme": TYPE_THEMES.get(qtype, qtype),
                "score": float(score),
                "id": row.get("id", ""),
            }
        )

    suggested = _diversify_hits(
        raw_hits, max_suggestions=max_suggestions, asked=asked
    )
    top_topic = suggested[0]["medical_topic"] if suggested else "none"

    return {
        "source": "medquad_assessment",
        "pack": top_topic,
        "red_flag_hints": GENERIC_RED_FLAGS,
        "suggested_questions": [
            {
                "topic": s["topic"],
                "theme": s.get("theme") or TYPE_THEMES.get(s["question_type"], s["question_type"]),
                "question_type": s["question_type"],
                "medical_topic": s["medical_topic"],
                "question": s["question"],
            }
            for s in suggested
        ],
        "known_fact_keys": list((known_facts or {}).keys()),
        "already_asked": list(asked),
        "query": query,
        "candidates": suggested,
        "type_priority": TYPE_PRIORITY,
    }
