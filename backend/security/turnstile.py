from __future__ import annotations

import os
from typing import Optional

import requests
from fastapi import HTTPException, Request

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def turnstile_enabled() -> bool:
    return bool((os.getenv("TURNSTILE_SECRET_KEY") or "").strip())


def verify_turnstile_token(
    token: Optional[str],
    *,
    remote_ip: Optional[str] = None,
) -> None:
    """
    Verify a Cloudflare Turnstile token with Siteverify.

    When TURNSTILE_SECRET_KEY is unset, verification is skipped (local/dev).
    When set, a valid token is required.
    """
    secret = (os.getenv("TURNSTILE_SECRET_KEY") or "").strip()
    if not secret:
        return

    if not token or not token.strip():
        raise HTTPException(
            status_code=400,
            detail="Bot check failed. Refresh the page and try again.",
        )

    payload: dict[str, str] = {
        "secret": secret,
        "response": token.strip(),
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        resp = requests.post(SITEVERIFY_URL, data=payload, timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Bot check temporarily unavailable. Try again shortly.",
        ) from exc

    if not data.get("success"):
        raise HTTPException(
            status_code=400,
            detail="Bot check failed. Refresh the page and try again.",
        )


def client_ip(request: Request) -> Optional[str]:
    forwarded = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if forwarded:
        return forwarded
    if request.client:
        return request.client.host
    return None
