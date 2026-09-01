"""Orchestrate knowledge retrieval + grounded guidance for LiveKit consultations."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from livekit_agent import config
from livekit_agent.events import log_event
from livekit_agent.guidance_agent import generate_guidance
from livekit_agent.knowledge_rag import retrieve_knowledge


def _ms_since(t0: float) -> int:
    return int((time.monotonic() - t0) * 1000)


async def run_knowledge_guidance(
    case_package: dict[str, Any],
    *,
    session_id: str = "-",
    turn_id: str = "-",
) -> dict[str, Any] | None:
    """
    Retrieve medical references and generate grounded guidance for a ready case package.

    Returns None when guidance is disabled or the package is not ready.
    """
    if not config.KNOWLEDGE_RAG_ENABLED:
        return None
    if not case_package.get("ready_for_retrieval"):
        return None

    final_query = str(case_package.get("final_query") or "").strip()
    if not final_query:
        return None

    t0 = time.monotonic()
    log_event(
        "RAG",
        "knowledge_retrieval_started",
        session_id=session_id,
        turn_id=turn_id,
        detail=f"mode={config.KNOWLEDGE_RAG_MODE} top_k={config.KNOWLEDGE_RAG_TOP_K}",
    )

    retrieval = await asyncio.to_thread(
        retrieve_knowledge,
        final_query,
        mode=config.KNOWLEDGE_RAG_MODE,
        top_k=config.KNOWLEDGE_RAG_TOP_K,
    )

    chunks = retrieval.get("chunks") or []
    retrieval_error = retrieval.get("error")
    log_event(
        "RAG",
        "knowledge_retrieval_finished",
        session_id=session_id,
        turn_id=turn_id,
        detail=(
            f"+{_ms_since(t0)}ms chunks={len(chunks)} "
            f"error={retrieval_error or 'none'}"
        ),
    )

    if retrieval_error or not chunks:
        return {
            "source": "knowledge_guidance",
            "final_query": final_query,
            "retrieval": retrieval,
            "guidance": None,
            "spoken_answer": "",
            "error": retrieval_error or "no_chunks",
        }

    log_event(
        "RAG",
        "guidance_generation_started",
        session_id=session_id,
        turn_id=turn_id,
        detail=f"+{_ms_since(t0)}ms model={config.GUIDANCE_MODEL}",
    )

    try:
        guidance = await generate_guidance(
            final_query=final_query,
            chief_complaint=case_package.get("chief_complaint"),
            facts=case_package.get("facts") or {},
            chunks=chunks,
        )
    except Exception as exc:
        log_event(
            "RAG",
            "guidance_generation_finished",
            session_id=session_id,
            turn_id=turn_id,
            detail=f"+{_ms_since(t0)}ms ok=false error={exc}",
        )
        return {
            "source": "knowledge_guidance",
            "final_query": final_query,
            "retrieval": retrieval,
            "guidance": None,
            "spoken_answer": "",
            "error": str(exc),
        }

    spoken = str(guidance.get("spoken_answer") or "").strip()
    log_event(
        "RAG",
        "guidance_generation_finished",
        session_id=session_id,
        turn_id=turn_id,
        detail=(
            f"+{_ms_since(t0)}ms ok=true spoken_chars={len(spoken)} "
            f"confidence={guidance.get('confidence')}"
        ),
    )

    return {
        "source": "knowledge_guidance",
        "final_query": final_query,
        "retrieval": retrieval,
        "guidance": guidance,
        "spoken_answer": spoken,
        "error": guidance.get("error"),
    }


async def _cli_main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Test knowledge guidance pipeline")
    parser.add_argument("query", help="Final consultation query text")
    args = parser.parse_args()

    package = {
        "final_query": args.query,
        "chief_complaint": args.query,
        "facts": {},
        "ready_for_retrieval": True,
    }
    result = await run_knowledge_guidance(package, session_id="cli", turn_id="1")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(_cli_main())
