"""
Build a small FAISS index over MedQuAD questions for assessment retrieval.

Separate from the large StatPearls knowledge index. Does not modify any
existing indexes or application code.

Usage:
  cd backend
  source venv/bin/activate
  python medical_rag/assessment/build_index.py

  python medical_rag/assessment/build_index.py --smoke-only
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import faiss
import numpy as np
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from questions import QUESTION_TEMPLATES, infer_question_type_from_text

CONFIG_PATH = ROOT / "config.json"


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def resolve_endpoint(cfg: dict) -> str:
    load_dotenv(ROOT.parent.parent / ".env")
    emb = cfg["embedding"]
    return os.getenv(emb["endpoint_env"]) or emb["default_endpoint"]


def infer_question_type(question: str) -> str:
    return infer_question_type_from_text(question)


def build_embed_text(topic: str, question: str, synonyms: list[str]) -> str:
    parts = [f"Topic: {topic}", f"Question: {question}"]
    if synonyms:
        parts.append(f"Synonyms: {', '.join(synonyms)}")
    return "\n".join(parts)


def normalize_medquad(medquad_path: Path) -> list[dict]:
    with medquad_path.open("r", encoding="utf-8") as f:
        docs = json.load(f)

    records: list[dict] = []
    for doc in docs:
        document_id = (doc.get("document_id") or "").strip()
        topic = (doc.get("title") or "").strip()
        qa_pairs = doc.get("qa_pairs") or []
        if not document_id or not topic or not qa_pairs:
            continue

        qa = qa_pairs[0] or {}
        original_question = (qa.get("question") or "").strip()
        answer = (qa.get("content") or "").strip()
        if not original_question:
            continue

        synonyms = [s for s in (doc.get("synonyms") or []) if s]
        base_meta = {
            "topic": topic,
            "synonyms": synonyms,
            "url": doc.get("url"),
            "origin": doc.get("source"),
            "document_id": document_id,
        }

        seen_types: set[str] = set()
        for qtype, template in QUESTION_TEMPLATES:
            question = template.format(topic=topic)
            seen_types.add(qtype)
            records.append(
                {
                    "id": f"assess_medquad_{document_id}_{qtype}",
                    "text": build_embed_text(topic, question, synonyms),
                    "topic": topic,
                    "question": question,
                    "answer": answer,
                    "metadata": {
                        **base_meta,
                        "question": question,
                        "question_type": qtype,
                        "source_question": original_question,
                    },
                }
            )

        # Keep original MedQuAD wording if it does not match a template type.
        orig_type = infer_question_type(original_question)
        if orig_type not in seen_types:
            records.append(
                {
                    "id": f"assess_medquad_{document_id}_original",
                    "text": build_embed_text(topic, original_question, synonyms),
                    "topic": topic,
                    "question": original_question,
                    "answer": answer,
                    "metadata": {
                        **base_meta,
                        "question": original_question,
                        "question_type": orig_type,
                        "source_question": original_question,
                    },
                }
            )

    return records


def truncate_for_embed(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars]


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-12)
    return (vectors / norms).astype(np.float32)


def embed_batch(
    endpoint: str,
    texts: list[str],
    timeout: int,
    max_retries: int,
    truncate_chars: int,
) -> list[list[float]]:
    texts = [truncate_for_embed(t, truncate_chars) for t in texts]
    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                endpoint, json={"inputs": texts}, timeout=timeout
            )
            if resp.status_code == 413 and len(texts) > 1:
                mid = len(texts) // 2
                left = embed_batch(
                    endpoint, texts[:mid], timeout, max_retries, truncate_chars
                )
                right = embed_batch(
                    endpoint, texts[mid:], timeout, max_retries, truncate_chars
                )
                return left + right
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, list) or len(data) != len(texts):
                raise RuntimeError(f"Unexpected embed response for batch of {len(texts)}")
            return data
        except Exception as exc:
            last_err = exc
            time.sleep(min(2**attempt, 30))
    raise RuntimeError(f"Embedding failed: {last_err}")


def embed_all(
    records: list[dict], endpoint: str, emb_cfg: dict
) -> np.ndarray:
    dim = int(emb_cfg["dimension"])
    batch_size = int(emb_cfg["batch_size"])
    timeout = int(emb_cfg["request_timeout_sec"])
    max_retries = int(emb_cfg["max_retries"])
    truncate_chars = int(emb_cfg.get("truncate_chars", 900))

    vectors = np.zeros((len(records), dim), dtype=np.float32)
    texts = [r["text"] for r in records]

    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        batch_vecs = l2_normalize(
            np.asarray(
                embed_batch(endpoint, batch, timeout, max_retries, truncate_chars),
                dtype=np.float32,
            )
        )
        vectors[start : start + len(batch)] = batch_vecs

    return vectors


def write_store(
    store_dir: Path,
    records: list[dict],
    vectors: np.ndarray,
    cfg: dict,
    endpoint: str,
) -> None:
    store_dir.mkdir(parents=True, exist_ok=True)

    corpus_path = store_dir / "corpus.jsonl"
    metadata_path = store_dir / "metadata.jsonl"
    index_path = store_dir / "index.faiss"

    with corpus_path.open("w", encoding="utf-8") as f:
        for row, rec in enumerate(records):
            f.write(
                json.dumps(
                    {
                        "row": row,
                        "id": rec["id"],
                        "text": rec["text"],
                        "topic": rec["topic"],
                        "question": rec["question"],
                        "metadata": rec["metadata"],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    with metadata_path.open("w", encoding="utf-8") as f:
        for row, rec in enumerate(records):
            f.write(
                json.dumps(
                    {
                        "row": row,
                        "id": rec["id"],
                        "topic": rec["topic"],
                        "question": rec["question"],
                        "answer": rec["answer"],
                        "text": rec["text"],
                        "metadata": rec["metadata"],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    dim = int(cfg["embedding"]["dimension"])
    index = faiss.IndexFlatIP(dim)
    index.add(np.ascontiguousarray(vectors, dtype=np.float32))
    faiss.write_index(index, str(index_path))

    store_cfg = {
        "version": cfg["version"],
        "purpose": "assessment_question_retrieval",
        "embedding": cfg["embedding"],
        "faiss": cfg["faiss"],
        "build": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "doc_count": len(records),
            "source": str((ROOT / cfg["paths"]["medquad"]).resolve()),
            "endpoint": endpoint,
            "model_id": cfg["embedding"]["model_id"],
        },
    }
    with (store_dir / "config.json").open("w", encoding="utf-8") as f:
        json.dump(store_cfg, f, indent=2)
        f.write("\n")


def smoke_test(store_dir: Path, endpoint: str, emb_cfg: dict) -> None:
    index = faiss.read_index(str(store_dir / "index.faiss"))
    metadata = [
        json.loads(line)
        for line in (store_dir / "metadata.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    queries = [
        "I have been very thirsty and urinating a lot",
        "severe headache with nausea",
        "chest pain and shortness of breath",
    ]

    print("\n" + "=" * 60)
    print("SMOKE TEST")
    print("=" * 60)
    for query in queries:
        vec = l2_normalize(
            np.asarray(
                embed_batch(
                    endpoint,
                    [query],
                    int(emb_cfg["request_timeout_sec"]),
                    int(emb_cfg["max_retries"]),
                    int(emb_cfg.get("truncate_chars", 900)),
                ),
                dtype=np.float32,
            )
        )
        scores, indices = index.search(vec, 3)
        print(f"\nQ: {query}")
        for rank, (idx, score) in enumerate(zip(indices[0], scores[0]), start=1):
            if idx < 0:
                continue
            m = metadata[int(idx)]
            qtype = (m.get("metadata") or {}).get("question_type", "?")
            print(
                f"  {rank}. [{score:.3f}] {qtype} | {m['topic']} | {m['question'][:70]}…"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build MedQuAD assessment index")
    parser.add_argument(
        "--smoke-only",
        action="store_true",
        help="Run smoke queries against an existing store",
    )
    args = parser.parse_args()

    cfg = load_config()
    medquad_path = (ROOT / cfg["paths"]["medquad"]).resolve()
    store_dir = (ROOT / cfg["paths"]["store_dir"]).resolve()
    endpoint = resolve_endpoint(cfg)
    emb_cfg = cfg["embedding"]

    if args.smoke_only:
        if not (store_dir / "index.faiss").is_file():
            raise SystemExit(f"Missing index at {store_dir}. Run build first.")
        smoke_test(store_dir, endpoint, emb_cfg)
        return

    if not medquad_path.is_file():
        raise SystemExit(f"MedQuAD file not found: {medquad_path}")

    print(f"MedQuAD  : {medquad_path}")
    print(f"Endpoint : {endpoint}")
    print(f"Store    : {store_dir}")

    records = normalize_medquad(medquad_path)
    if not records:
        raise SystemExit("No assessment records produced from MedQuAD.")

    print(f"Records  : {len(records)}")
    print("Embedding …")
    vectors = embed_all(records, endpoint, emb_cfg)

    if vectors.shape != (len(records), int(emb_cfg["dimension"])):
        raise SystemExit(f"Bad embedding shape: {vectors.shape}")

    write_store(store_dir, records, vectors, cfg, endpoint)
    print(f"\nWrote {store_dir / 'index.faiss'}")
    print(f"Wrote {store_dir / 'metadata.jsonl'}")
    print(f"Wrote {store_dir / 'config.json'}")

    smoke_test(store_dir, endpoint, emb_cfg)
    print("\nDone.")


if __name__ == "__main__":
    main()
