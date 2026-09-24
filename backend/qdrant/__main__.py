"""python -m qdrant  → connectivity smoke test."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from qdrant import config
from qdrant.client import ping


def main() -> int:
    if not config.is_configured():
        print("FAIL: set QDRANT_URL and QDRANT_API_KEY in backend/.env")
        return 1

    host = config.url_host() or "(unknown)"
    print(f"Connecting to {host} …")
    try:
        status = ping()
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}")
        return 1

    print("OK: connected to Qdrant")
    print(f"  collections: {status['collection_count']}")
    if status["collections"]:
        for name in status["collections"]:
            print(f"    - {name}")
    else:
        print("    (none yet — expected before upload)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
