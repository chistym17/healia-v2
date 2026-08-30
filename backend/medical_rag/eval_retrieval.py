"""
Retrieval evaluation over the medical corpus.

Reports exact Recall@k plus soft Useful@k / Related@k.

Modes:
  --mode faiss     dense baseline (default)
  --mode bm25      lexical only
  --mode hybrid    FAISS + BM25 via RRF
  --mode rerank    hybrid candidates + BGE reranker
  --mode compare   FAISS vs Hybrid vs Hybrid+Rerank

Usage:
  cd backend
  source venv/bin/activate
  python medical_rag/eval_retrieval.py --mode compare --quiet
  python medical_rag/eval_retrieval.py --mode rerank --quiet
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

from retrieve import MedicalRetriever

ROOT = Path(__file__).resolve().parent
EVAL_SET_PATH = ROOT / "eval" / "retrieval_eval_set.json"
K_VALUES = (1, 3, 5, 10)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def norm_key(value: str) -> str:
    return (value or "").strip().lower()


def soft_grade(meta: dict, gold_topic: str, gold_section: str) -> int:
    md = meta.get("metadata") or {}
    topic = norm_key(md.get("topic", ""))
    section = norm_key(md.get("section", ""))
    gt = norm_key(gold_topic)
    gs = norm_key(gold_section)

    if not gt or topic != gt:
        return 0
    if gs and section == gs:
        return 2
    return 1


def recall_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    return 1.0 if set(retrieved_ids[:k]).intersection(relevant_ids) else 0.0


def any_grade_at_k(grades: list[int], k: int, min_grade: int) -> float:
    return 1.0 if any(g >= min_grade for g in grades[:k]) else 0.0


def evaluate_mode(
    retriever: MedicalRetriever,
    cases: list[dict],
    mode: str,
    verbose: bool,
) -> dict[str, dict[int, list[float]]]:
    exact = {k: [] for k in K_VALUES}
    useful = {k: [] for k in K_VALUES}
    related = {k: [] for k in K_VALUES}
    max_k = max(K_VALUES)

    if verbose:
        print("\n" + "=" * 72)
        print(f"PER-QUESTION RESULTS — {mode}")
        print("=" * 72)

    for case in cases:
        q = case["question"]
        gold = case["relevant_ids"]
        gold_topic = case["topic"]
        gold_section = case["section"]

        hits = retriever.search(q, mode=mode, top_k=max_k)
        retrieved_ids = [h["id"] for h in hits]
        grades = [soft_grade(h, gold_topic, gold_section) for h in hits]

        if verbose:
            print(f"\n[{case['id']}] {q}")
            print(f"  gold: {gold}  ({gold_topic} -- {gold_section})")
            for rank, (hit, grade) in enumerate(zip(hits, grades), start=1):
                mark = "HIT" if hit["id"] in gold else "   "
                topic = (hit.get("metadata") or {}).get("topic", "")
                section = (hit.get("metadata") or {}).get("section", "")
                label = f"{topic} -- {section}".strip(" -")
                print(
                    f"  {mark} g={grade} @{rank} [{hit['score']:.3f}] {hit['id']}"
                )
                if label:
                    print(f"         {label}")

        for k in K_VALUES:
            exact[k].append(recall_at_k(retrieved_ids, gold, k))
            useful[k].append(any_grade_at_k(grades, k, min_grade=2))
            related[k].append(any_grade_at_k(grades, k, min_grade=1))

    return {"exact": exact, "useful": useful, "related": related}


def print_summary(label: str, metrics: dict, n: int) -> None:
    print("\n" + "=" * 72)
    print(f"SUMMARY — {label} — Exact chunk-ID recall")
    print("=" * 72)
    for k in K_VALUES:
        mean = sum(metrics["exact"][k]) / n
        hits = int(sum(metrics["exact"][k]))
        print(f"Recall@{k:<2}   {mean:.2f}  ({hits}/{n})")

    print("\n" + "=" * 72)
    print(f"SUMMARY — {label} — Soft / practical relevance")
    print("=" * 72)
    print("Useful@k  = grade-2 (same topic + section)")
    print("Related@k = grade-1+ (same topic)")
    print()
    for k in K_VALUES:
        u_mean = sum(metrics["useful"][k]) / n
        u_hits = int(sum(metrics["useful"][k]))
        r_mean = sum(metrics["related"][k]) / n
        r_hits = int(sum(metrics["related"][k]))
        print(
            f"Useful@{k:<2}   {u_mean:.2f}  ({u_hits}/{n})   |   "
            f"Related@{k:<2}  {r_mean:.2f}  ({r_hits}/{n})"
        )


def print_compare(results: dict[str, dict], n: int) -> None:
    labels = list(results.keys())
    print("\n" + "=" * 72)
    print("COMPARE — " + " vs ".join(labels))
    print("=" * 72)
    header = f"{'Metric':<14}" + "".join(f"{lab:>12}" for lab in labels)
    print(header)
    for name, key in (("Recall", "exact"), ("Useful", "useful"), ("Related", "related")):
        for k in K_VALUES:
            row = f"{name}@{k:<2}       "
            for lab in labels:
                mean = sum(results[lab][key][k]) / n
                row += f"{mean:>12.2f}"
            print(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate medical retrieval")
    parser.add_argument(
        "--mode",
        choices=("faiss", "bm25", "hybrid", "rerank", "compare"),
        default="faiss",
        help="Retrieval mode (default: faiss)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print summaries (no per-question dumps)",
    )
    args = parser.parse_args()

    if not EVAL_SET_PATH.is_file():
        raise SystemExit(f"Missing eval set: {EVAL_SET_PATH}")

    cases = load_json(EVAL_SET_PATH)
    for case in cases:
        if not case.get("topic") or not case.get("section"):
            raise SystemExit(f"Case {case.get('id')} missing topic/section")

    need_bm25 = args.mode in ("bm25", "hybrid", "rerank", "compare")
    print(f"Eval set : {EVAL_SET_PATH} ({len(cases)} questions)")
    print(f"Mode     : {args.mode}")
    print("Loading retriever …")
    retriever = MedicalRetriever(load_bm25=need_bm25)
    print(f"FAISS    : {retriever.faiss_index.ntotal} vectors")
    if need_bm25:
        retriever.require_bm25()
        print(f"BM25     : {len(retriever.bm25_doc_ids)} docs")
    print(f"Embed    : {retriever.endpoint}")
    if args.mode in ("rerank", "compare"):
        print(f"Rerank   : {retriever.rerank_endpoint}")
    print("Soft grades: 0=irrelevant  1=same topic  2=same topic+section")

    verbose = not args.quiet
    n = len(cases)

    if args.mode == "compare":
        results = {
            "FAISS": evaluate_mode(retriever, cases, "faiss", verbose=verbose),
            "Hybrid": evaluate_mode(retriever, cases, "hybrid", verbose=verbose),
            "Rerank": evaluate_mode(retriever, cases, "rerank", verbose=verbose),
        }
        for label, metrics in results.items():
            print_summary(label, metrics, n)
        print_compare(results, n)
    else:
        metrics = evaluate_mode(retriever, cases, args.mode, verbose=verbose)
        label = "HYBRID+RERANK" if args.mode == "rerank" else args.mode.upper()
        print_summary(label, metrics, n)

    print()


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
