from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from auth.supabase_auth import (
    get_current_user,
    login_email,
    refresh_session,
    signup_email,
)
from security.rate_limit import limit_ip
from security.turnstile import client_ip, verify_turnstile_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=120)
    turnstile_token: str | None = Field(default=None, max_length=2048)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/signup")
def signup(
    body: SignupRequest,
    request: Request,
    _: None = Depends(limit_ip("auth_signup", 5, 60.0)),
) -> dict[str, Any]:
    verify_turnstile_token(body.turnstile_token, remote_ip=client_ip(request))
    try:
        return signup_email(body.email, body.password, body.display_name)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login")
def login(
    body: LoginRequest,
    _: None = Depends(limit_ip("auth_login", 10, 60.0)),
) -> dict[str, Any]:
    try:
        return login_email(body.email, body.password)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/refresh")
def refresh(
    body: RefreshRequest,
    _: None = Depends(limit_ip("auth_refresh", 20, 60.0)),
) -> dict[str, Any]:
    try:
        return refresh_session(body.refresh_token)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/me")
def me(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return {"user": user}
