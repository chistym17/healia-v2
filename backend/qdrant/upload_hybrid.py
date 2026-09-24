"""Upload local FAISS stores to Qdrant with dense + sparse BM25 vectors."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND / ".env")

from qdrant import config
from qdrant.client import get_client
from qdrant.collections import collection_info, ensure_hybrid_collection
from qdrant.export import (
    ASSESSMENT_STORE,
    KNOWLEDGE_STORE,
    assessment_payload,
    count_metadata,
    iter_point_batches,
    knowledge_payload,
)
from qdrant.sparse import text_to_sparse


def _upsert_hybrid(
    *,
    collection: str,
    store_dir: Path,
    payload_fn,
    batch_size: int,
    recreate: bool,
) -> None:
    from qdrant_client.models import PointStruct

    if not store_dir.is_dir():
        raise FileNotFoundError(f"Store not found: {store_dir}")

    total = count_metadata(store_dir)
    print(f"Collection : {collection} (dense + sparse BM25)")
    print(f"Store      : {store_dir}")
    print(f"Points     : {total}")
    print(f"Batch size : {batch_size}")

    created = ensure_hybrid_collection(collection, recreate=recreate)
    print(f"{'Recreated' if recreate else 'Ensured'} collection (new={created})")

    client = get_client()
    uploaded = 0
    t0 = time.monotonic()

    for ids, vectors, payloads in iter_point_batches(
        store_dir, payload_fn=payload_fn, batch_size=batch_size
    ):
        points = []
        for i, vec, payload in zip(ids, vectors, payloads):
            text = str(payload.get("text") or payload.get("question") or "")
            points.append(
                PointStruct(
                    id=i,
                    vector={
                        config.DENSE_VECTOR: vec,
                        config.SPARSE_VECTOR: text_to_sparse(text),
                    },
                    payload=payload,
                )
            )
        client.upsert(collection_name=collection, points=points, wait=True)
        uploaded += len(points)
        elapsed = time.monotonic() - t0
        rate = uploaded / elapsed if elapsed > 0 else 0
        pct = 100.0 * uploaded / total if total else 100.0
        print(
            f"  {uploaded}/{total} ({pct:.1f}%)  "
            f"{rate:.0f} pts/s  elapsed {elapsed:.0f}s",
            flush=True,
        )

    info = collection_info(collection)
    print(
        f"Done. points_count={info.get('points_count')} status={info.get('status')}"
    )


def upload_assessment(*, batch_size: int = 128, recreate: bool = False) -> None:
    _upsert_hybrid(
        collection=config.ASSESSMENT_COLLECTION,
        store_dir=ASSESSMENT_STORE,
        payload_fn=assessment_payload,
        batch_size=batch_size,
        recreate=recreate,
    )


def upload_knowledge(*, batch_size: int = 64, recreate: bool = False) -> None:
    _upsert_hybrid(
        collection=config.KNOWLEDGE_COLLECTION,
        store_dir=KNOWLEDGE_STORE,
        payload_fn=knowledge_payload,
        batch_size=batch_size,
        recreate=recreate,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Upload Healia indexes to Qdrant (dense + BM25 sparse)"
    )
    parser.add_argument(
        "target",
        choices=("assessment", "knowledge", "all"),
        help="Which local store to upload",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate the hybrid collection before upload",
    )
    parser.add_argument("--batch-size", type=int, default=0, help="Upsert batch size")
    args = parser.parse_args(argv)

    if not config.is_configured():
        print("FAIL: set QDRANT_URL and QDRANT_API_KEY in backend/.env")
        return 1

    try:
        if args.target in ("assessment", "all"):
            batch = args.batch_size or 128
            upload_assessment(batch_size=batch, recreate=args.recreate)
        if args.target in ("knowledge", "all"):
            batch = args.batch_size or 64
            upload_knowledge(batch_size=batch, recreate=args.recreate)
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
