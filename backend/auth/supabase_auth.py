from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

from db.sessions import ensure_user, get_user

_bearer = HTTPBearer(auto_error=False)


def _require_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


@lru_cache
def get_supabase_anon() -> Client:
    return create_client(_require_env("SUPABASE_URL"), _require_env("SUPABASE_ANON_KEY"))


def _session_payload(session: Any, user_row: dict[str, Any]) -> dict[str, Any]:
    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "expires_in": session.expires_in,
        "token_type": getattr(session, "token_type", "bearer"),
        "user": {
            "id": str(user_row["id"]),
            "email": user_row["email"],
            "display_name": user_row.get("display_name"),
        },
    }


def sync_profile_from_auth_user(auth_user: Any) -> dict[str, Any]:
    meta = getattr(auth_user, "user_metadata", None) or {}
    if isinstance(meta, dict):
        display_name = meta.get("display_name") or meta.get("full_name") or meta.get("name")
    else:
        display_name = None
    return ensure_user(
        user_id=str(auth_user.id),
        email=str(auth_user.email or ""),
        display_name=display_name,
    )


def signup_email(email: str, password: str, display_name: str | None = None) -> dict[str, Any]:
    client = get_supabase_anon()
    payload: dict[str, Any] = {"email": email, "password": password}
    if display_name:
        payload["options"] = {"data": {"display_name": display_name}}
    result = client.auth.sign_up(payload)
    if not result.user:
        raise HTTPException(status_code=400, detail="Signup failed")
    user_row = sync_profile_from_auth_user(result.user)
    if not result.session:
        return {
            "user": {
                "id": str(user_row["id"]),
                "email": user_row["email"],
                "display_name": user_row.get("display_name"),
            },
            "session": None,
            "message": "Check your email to confirm signup, then log in.",
        }
    return _session_payload(result.session, user_row)


def login_email(email: str, password: str) -> dict[str, Any]:
    client = get_supabase_anon()
    result = client.auth.sign_in_with_password({"email": email, "password": password})
    if not result.session or not result.user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user_row = sync_profile_from_auth_user(result.user)
    return _session_payload(result.session, user_row)


def refresh_session(refresh_token: str) -> dict[str, Any]:
    client = get_supabase_anon()
    result = client.auth.refresh_session(refresh_token)
    if not result.session or not result.user:
        raise HTTPException(status_code=401, detail="Could not refresh session")
    user_row = sync_profile_from_auth_user(result.user)
    return _session_payload(result.session, user_row)


def user_from_access_token(token: str) -> dict[str, Any]:
    client = get_supabase_anon()
    result = client.auth.get_user(token)
    auth_user = result.user
    if not auth_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_row = get_user(str(auth_user.id))
    if not user_row:
        user_row = sync_profile_from_auth_user(auth_user)
    return {
        "id": str(user_row["id"]),
        "email": user_row["email"],
        "display_name": user_row.get("display_name"),
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any]:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    return user_from_access_token(credentials.credentials)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any] | None:
    if not credentials or not credentials.credentials:
        return None
    try:
        return user_from_access_token(credentials.credentials)
    except HTTPException:
        return None
