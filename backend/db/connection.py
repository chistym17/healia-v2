from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


def _database_url() -> str:
    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


@contextmanager
def get_conn() -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(
        _database_url(),
        row_factory=dict_row,
        prepare_threshold=None,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_one(query: str, params: tuple[Any, ...] | dict[str, Any] | None = None) -> dict[str, Any] | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()


def fetch_all(query: str, params: tuple[Any, ...] | dict[str, Any] | None = None) -> list[dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return list(cur.fetchall())


def execute(query: str, params: tuple[Any, ...] | dict[str, Any] | None = None) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)


def as_jsonb(value: Any) -> Jsonb:
    return Jsonb(value if value is not None else None)
