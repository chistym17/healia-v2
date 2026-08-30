"""
Build a FAISS IndexFlatIP over the normalized medical corpus.

Uses the local TEI embedder (MiniLM-L6-v2). Embeddings are checkpointed so
an interrupted run can resume. Does not modify the corpus or the old
symptom vectorstore.

Usage:
  cd backend
  source venv/bin/activate
  python medical_rag/build_index.py

  python medical_rag/build_index.py --force      # wipe checkpoints / store and restart
  python medical_rag/build_index.py --smoke-only # search only (index must exist)
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import faiss
import numpy as np
import requests
from dotenv import load_dotenv

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover
    def tqdm(iterable, **kwargs):
        return iterable


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def resolve_endpoint(cfg: dict) -> str:
    load_dotenv(ROOT.parent / ".env")
    emb = cfg["embedding"]
    return os.getenv(emb["endpoint_env"]) or emb["default_endpoint"]


def count_corpus_lines(path: Path) -> int:
    n = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def write_metadata(corpus_path: Path, metadata_path: Path) -> int:
    """Write one metadata row per corpus doc (aligned by line index)."""
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with corpus_path.open("r", encoding="utf-8") as src, metadata_path.open(
        "w", encoding="utf-8"
    ) as dst:
        for line in src:
            line = line.strip()
            if not line:
                continue
            doc = json.loads(line)
            row = {
                "row": n,
                "id": doc["id"],
                "source": doc["source"],
                "text": doc["text"],
                "metadata": doc.get("metadata") or {},
            }
            dst.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def count_metadata_rows(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-12)
    return (vectors / norms).astype(np.float32)


def truncate_for_embed(text: str, max_chars: int) -> str:
    """TEI MiniLM rejects inputs with >= 256 tokens; truncate embed text only."""
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars]


def embed_batch(
    endpoint: str,
    texts: list[str],
    timeout: int,
    max_retries: int,
    truncate_chars: int = 900,
) -> list[list[float]]:
    """Embed texts; truncate to TEI limit; on 413, split or shorten further."""
    if not texts:
        return []

    texts = [truncate_for_embed(t, truncate_chars) for t in texts]

    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                endpoint,
                json={"inputs": texts},
                timeout=timeout,
            )
            if resp.status_code == 413:
                if len(texts) > 1:
                    mid = len(texts) // 2
                    print(
                        f"  413 batch too large (n={len(texts)}); "
                        f"splitting to {mid}+{len(texts) - mid}"
                    )
                    left = embed_batch(
                        endpoint, texts[:mid], timeout, max_retries, truncate_chars
                    )
                    right = embed_batch(
                        endpoint, texts[mid:], timeout, max_retries, truncate_chars
                    )
                    return left + right

                # Single oversize text: shorten and retry (metadata still has full text)
                shorter = max(truncate_chars // 2, 200)
                if len(texts[0]) > shorter:
                    print(
                        f"  413 single text ({len(texts[0])} chars); "
                        f"retrying at {shorter} chars"
                    )
                    return embed_batch(
                        endpoint, [texts[0][:shorter]], timeout, max_retries, shorter
                    )

            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, list) or len(data) != len(texts):
                raise RuntimeError(
                    f"Unexpected embed response: got {type(data)} "
                    f"len={len(data) if isinstance(data, list) else 'n/a'}, "
                    f"expected {len(texts)}"
                )
            return data
        except Exception as exc:
            last_err = exc
            sleep_s = min(2 ** attempt, 30)
            print(f"  embed retry {attempt}/{max_retries}: {exc} (sleep {sleep_s}s)")
            time.sleep(sleep_s)
    raise RuntimeError(f"Embedding failed after {max_retries} retries: {last_err}")


def load_progress(path: Path) -> dict | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_progress(path: Path, progress: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)
    tmp.replace(path)


def open_embedding_memmap(
    path: Path,
    n: int,
    dim: int,
    resume: bool,
) -> np.memmap:
    path.parent.mkdir(parents=True, exist_ok=True)
    if resume and path.exists():
        emb = np.lib.format.open_memmap(path, mode="r+")
        if emb.shape != (n, dim):
            raise SystemExit(
                f"Checkpoint shape {emb.shape} != expected {(n, dim)}. "
                "Use --force to rebuild."
            )
        return emb
    return np.lib.format.open_memmap(
        path, mode="w+", dtype=np.float32, shape=(n, dim)
    )


def iter_corpus_texts(corpus_path: Path):
    with corpus_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)["text"]


def embed_corpus(
    cfg: dict,
    corpus_path: Path,
    checkpoint_dir: Path,
    n_docs: int,
    endpoint: str,
) -> np.memmap:
    emb_cfg = cfg["embedding"]
    dim = emb_cfg["dimension"]
    batch_size = emb_cfg["batch_size"]
    save_every = cfg["checkpoint"]["save_every_batches"]
    timeout = emb_cfg["request_timeout_sec"]
    max_retries = emb_cfg["max_retries"]
    truncate_chars = int(emb_cfg.get("truncate_chars", 900))

    emb_path = checkpoint_dir / "embeddings.npy"
    progress_path = checkpoint_dir / "progress.json"

    progress = load_progress(progress_path)
    resume = False
    start_row = 0

    if progress and progress.get("status") != "complete":
        if (
            progress.get("model_id") != emb_cfg["model_id"]
            or progress.get("dimension") != dim
            or progress.get("corpus_count") != n_docs
            or progress.get("normalize") != emb_cfg["normalize"]
        ):
            raise SystemExit(
                "Checkpoint config mismatch. Use --force to restart, or fix config."
            )
        start_row = int(progress.get("next_row", 0))
        resume = start_row > 0
        print(f"Resuming embeddings from row {start_row}/{n_docs}")

    emb = open_embedding_memmap(emb_path, n_docs, dim, resume=resume)

    if start_row >= n_docs:
        print("Embeddings already complete.")
        return emb

    # Stream corpus; skip already-done rows
    batch_texts: list[str] = []
    batch_start = start_row
    row = 0
    batches_since_save = 0

    pbar = tqdm(
        total=n_docs,
        initial=start_row,
        desc="Embedding",
        unit="doc",
    )

    for text in iter_corpus_texts(corpus_path):
        if row < start_row:
            row += 1
            continue

        if not batch_texts:
            batch_start = row
        batch_texts.append(text)
        row += 1

        if len(batch_texts) < batch_size and row < n_docs:
            continue

        vectors = embed_batch(
            endpoint, batch_texts, timeout, max_retries, truncate_chars
        )
        arr = l2_normalize(np.asarray(vectors, dtype=np.float32))
        if arr.shape != (len(batch_texts), dim):
            raise RuntimeError(f"Bad batch shape {arr.shape}")

        emb[batch_start : batch_start + len(batch_texts)] = arr
        pbar.update(len(batch_texts))
        batch_texts = []
        batches_since_save += 1

        if batches_since_save >= save_every or row >= n_docs:
            emb.flush()
            save_progress(
                progress_path,
                {
                    "status": "embedding",
                    "next_row": row,
                    "corpus_count": n_docs,
                    "model_id": emb_cfg["model_id"],
                    "dimension": dim,
                    "normalize": emb_cfg["normalize"],
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            batches_since_save = 0

    pbar.close()
    emb.flush()
    save_progress(
        progress_path,
        {
            "status": "complete",
            "next_row": n_docs,
            "corpus_count": n_docs,
            "model_id": emb_cfg["model_id"],
            "dimension": dim,
            "normalize": emb_cfg["normalize"],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return emb


def build_faiss(emb: np.memmap, dim: int, index_path: Path) -> int:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    # FAISS needs a contiguous float32 array; for large N load in chunks into index
    index = faiss.IndexFlatIP(dim)
    n = emb.shape[0]
    chunk = 50_000
    for start in tqdm(range(0, n, chunk), desc="FAISS add"):
        end = min(start + chunk, n)
        block = np.ascontiguousarray(emb[start:end], dtype=np.float32)
        index.add(block)
    faiss.write_index(index, str(index_path))
    return index.ntotal


def write_store_config(cfg: dict, store_dir: Path, build_info: dict) -> None:
    store_dir.mkdir(parents=True, exist_ok=True)
    frozen = {
        "version": cfg["version"],
        "embedding": cfg["embedding"],
        "faiss": cfg["faiss"],
        "build": build_info,
    }
    with (store_dir / "config.json").open("w", encoding="utf-8") as f:
        json.dump(frozen, f, indent=2)
        f.write("\n")


def build_metadata_offsets(metadata_path: Path) -> list[int]:
    offsets: list[int] = []
    with metadata_path.open("rb") as f:
        while True:
            pos = f.tell()
            line = f.readline()
            if not line:
                break
            if line.strip():
                offsets.append(pos)
    return offsets


def load_metadata_at(metadata_path: Path, offsets: list[int], row: int) -> dict:
    with metadata_path.open("rb") as f:
        f.seek(offsets[row])
        return json.loads(f.readline().decode("utf-8"))


def smoke_test(cfg: dict, store_dir: Path, endpoint: str) -> None:
    index_path = store_dir / "index.faiss"
    metadata_path = store_dir / "metadata.jsonl"
    store_cfg_path = store_dir / "config.json"

    if not index_path.exists() or not metadata_path.exists():
        raise SystemExit("Store incomplete; run a full build first.")

    with store_cfg_path.open("r", encoding="utf-8") as f:
        store_cfg = json.load(f)

    top_k = cfg.get("smoke_top_k", 5)
    index = faiss.read_index(str(index_path))
    offsets = build_metadata_offsets(metadata_path)

    print("\n" + "=" * 60)
    print("SMOKE TEST")
    print("=" * 60)

    for query in cfg["smoke_queries"]:
        vecs = embed_batch(
            endpoint,
            [query],
            store_cfg["embedding"]["request_timeout_sec"],
            store_cfg["embedding"]["max_retries"],
            int(store_cfg["embedding"].get("truncate_chars", 900)),
        )
        q = l2_normalize(np.asarray(vecs, dtype=np.float32))
        scores, indices = index.search(q, top_k)

        print(f"\nQ: {query}")
        for rank, (idx, score) in enumerate(zip(indices[0], scores[0]), start=1):
            if idx < 0:
                continue
            meta = load_metadata_at(metadata_path, offsets, int(idx))
            preview = meta["text"].replace("\n", " ")[:160]
            print(
                f"  {rank}. [{score:.3f}] {meta['id']} ({meta['source']})\n"
                f"     {preview}…"
            )


def clear_artifacts(checkpoint_dir: Path, store_dir: Path) -> None:
    for d in (checkpoint_dir, store_dir):
        if not d.exists():
            continue
        for p in d.iterdir():
            if p.is_file():
                p.unlink()
        print(f"Cleared {d}")


def validate_counts(n_corpus: int, n_meta: int, n_emb: int, n_faiss: int) -> None:
    print("\n" + "=" * 60)
    print("COUNT VALIDATION")
    print("=" * 60)
    print(f"corpus docs     : {n_corpus}")
    print(f"metadata rows   : {n_meta}")
    print(f"embeddings      : {n_emb}")
    print(f"FAISS vectors   : {n_faiss}")
    if not (n_corpus == n_meta == n_emb == n_faiss):
        raise SystemExit("Count mismatch — index is invalid.")
    print("OK: all counts match.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build medical corpus FAISS index")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete checkpoints and store, then rebuild from scratch",
    )
    parser.add_argument(
        "--smoke-only",
        action="store_true",
        help="Run smoke queries against an existing store",
    )
    args = parser.parse_args()

    cfg = load_config()
    corpus_path = (ROOT / cfg["paths"]["corpus"]).resolve()
    store_dir = (ROOT / cfg["paths"]["store_dir"]).resolve()
    checkpoint_dir = (ROOT / cfg["paths"]["checkpoint_dir"]).resolve()
    endpoint = resolve_endpoint(cfg)

    store_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    if args.smoke_only:
        smoke_test(cfg, store_dir, endpoint)
        return

    if not corpus_path.is_file():
        raise SystemExit(f"Corpus not found: {corpus_path}")

    if args.force:
        clear_artifacts(checkpoint_dir, store_dir)

    print(f"Config     : {CONFIG_PATH}")
    print(f"Corpus     : {corpus_path}")
    print(f"Endpoint   : {endpoint}")
    print(f"Checkpoints: {checkpoint_dir}")
    print(f"Store      : {store_dir}")

    # Verify TEI model matches freeze
    try:
        info = requests.get(endpoint.replace("/embed", "/info"), timeout=10).json()
        tei_model = info.get("model_id")
        print(f"TEI model  : {tei_model}")
        if tei_model != cfg["embedding"]["model_id"]:
            raise SystemExit(
                f"TEI model {tei_model!r} != config {cfg['embedding']['model_id']!r}"
            )
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(f"Cannot reach TEI info endpoint: {exc}") from exc

    n_corpus = count_corpus_lines(corpus_path)
    print(f"Corpus docs: {n_corpus}")

    metadata_path = store_dir / "metadata.jsonl"
    n_meta = count_metadata_rows(metadata_path)
    if n_meta != n_corpus:
        print("Writing metadata.jsonl …")
        n_meta = write_metadata(corpus_path, metadata_path)
    else:
        print("metadata.jsonl already complete.")

    emb = embed_corpus(cfg, corpus_path, checkpoint_dir, n_corpus, endpoint)
    n_emb = emb.shape[0]
    dim = cfg["embedding"]["dimension"]
    if emb.shape[1] != dim:
        raise SystemExit(f"Embedding dim {emb.shape[1]} != config {dim}")

    index_path = store_dir / "index.faiss"
    print("Building FAISS IndexFlatIP …")
    n_faiss = build_faiss(emb, dim, index_path)

    validate_counts(n_corpus, n_meta, n_emb, n_faiss)

    build_info = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "corpus_path": str(corpus_path),
        "corpus_docs": n_corpus,
        "embeddings": n_emb,
        "faiss_vectors": n_faiss,
        "metadata_rows": n_meta,
        "model_id": cfg["embedding"]["model_id"],
        "dimension": dim,
        "normalize": cfg["embedding"]["normalize"],
        "faiss_index_type": cfg["faiss"]["index_type"],
        "config_version": cfg["version"],
        "endpoint": endpoint,
    }
    write_store_config(cfg, store_dir, build_info)

    print(f"\nWrote {index_path}")
    print(f"Wrote {metadata_path}")
    print(f"Wrote {store_dir / 'config.json'}")

    smoke_test(cfg, store_dir, endpoint)
    print("\nDone.")


if __name__ == "__main__":
    main()
