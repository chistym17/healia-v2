from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque
from typing import Any

from fastapi import Depends, HTTPException, Request


class RateLimiter:
    """Simple in-memory fixed-window rate limiter (portfolio / single-instance)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def hit(self, key: str, *, limit: int, window_sec: float) -> None:
        now = time.monotonic()
        cutoff = now - window_sec
        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please wait a moment and try again.",
                )
            bucket.append(now)


_limiter = RateLimiter()


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def limit_ip(scope: str, limit: int, window_sec: float = 60.0):
    async def _dep(request: Request) -> None:
        _limiter.hit(
            f"{scope}:ip:{client_ip(request)}",
            limit=limit,
            window_sec=window_sec,
        )

    return _dep


def limit_user(scope: str, limit: int, window_sec: float = 60.0):
    from auth.supabase_auth import get_current_user

    async def _dep(
        request: Request,
        user: dict[str, Any] = Depends(get_current_user),
    ) -> None:
        uid = user.get("id") or client_ip(request)
        _limiter.hit(
            f"{scope}:user:{uid}",
            limit=limit,
            window_sec=window_sec,
        )

    return _dep


def cors_origins() -> list[str]:
    raw = (os.getenv("CORS_ORIGINS") or "").strip()
    if not raw or raw == "*":
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    return [o.strip() for o in raw.split(",") if o.strip()]


def docs_enabled() -> bool:
    raw = (os.getenv("ENABLE_DOCS") or "true").strip().lower()
    return raw not in ("0", "false", "no", "off")
