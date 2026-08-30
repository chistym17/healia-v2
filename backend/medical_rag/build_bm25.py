"""
Build a persisted BM25 index aligned with the FAISS / metadata row order.

Does NOT modify FAISS embeddings or store/.

Uses store/metadata.jsonl `text` field so BM25 row i == FAISS vector i.

Usage:
  cd backend
  source venv/bin/activate
  python medical_rag/build_bm25.py
  python medical_rag/build_bm25.py --force
"""

from __future__ import annotations

import argparse
import json
import pickle
import re
from datetime import datetime, timezone
from pathlib import Path

from rank_bm25 import BM25Okapi

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover
    def tqdm(iterable, **kwargs):
        return iterable


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"

TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def main() -> None:
    parser = argparse.ArgumentParser(description="Build BM25 index for medical corpus")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing BM25 index",
    )
    args = parser.parse_args()

    cfg = load_config()
    store_dir = (ROOT / cfg["paths"]["store_dir"]).resolve()
    bm25_dir = (ROOT / cfg["paths"]["bm25_dir"]).resolve()
    metadata_path = store_dir / "metadata.jsonl"

    if not metadata_path.is_file():
        raise SystemExit(
            f"Missing {metadata_path}. Build the FAISS store first "
            "(python medical_rag/build_index.py)."
        )

    bm25_dir.mkdir(parents=True, exist_ok=True)
    index_path = bm25_dir / "bm25.pkl"
    meta_path = bm25_dir / "meta.json"

    if index_path.exists() and not args.force:
        raise SystemExit(
            f"BM25 index already exists at {index_path}. Use --force to rebuild."
        )

    print(f"Reading metadata: {metadata_path}")
    doc_ids: list[str] = []
    tokenized: list[list[str]] = []

    with metadata_path.open("r", encoding="utf-8") as f:
        for line in tqdm(f, desc="Tokenizing"):
            if not line.strip():
                continue
            row = json.loads(line)
            expected = len(doc_ids)
            if int(row["row"]) != expected:
                raise SystemExit(
                    f"Row alignment broken at metadata row={row['row']} "
                    f"expected={expected}"
                )
            doc_ids.append(row["id"])
            tokenized.append(tokenize(row.get("text") or ""))

    n = len(doc_ids)
    print(f"Documents: {n}")
    print("Fitting BM25Okapi …")
    bm25_cfg = cfg.get("bm25", {})
    bm25 = BM25Okapi(
        tokenized,
        k1=float(bm25_cfg.get("k1", 1.5)),
        b=float(bm25_cfg.get("b", 0.75)),
    )

    # Drop raw token lists from memory before pickle? BM25Okapi keeps corpus.
    payload = {
        "bm25": bm25,
        "doc_ids": doc_ids,
    }
    print(f"Writing {index_path} …")
    with index_path.open("wb") as f:
        pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)

    meta = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "doc_count": n,
        "source": str(metadata_path),
        "aligned_with": "store/metadata.jsonl + store/index.faiss row order",
        "k1": float(bm25_cfg.get("k1", 1.5)),
        "b": float(bm25_cfg.get("b", 0.75)),
        "tokenizer": "regex [a-z0-9]+ lowercased",
    }
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")

    print("\nBM25 index ready.")
    print(f"  docs : {n}")
    print(f"  index: {index_path}")
    print(f"  meta : {meta_path}")


if __name__ == "__main__":
    main()
