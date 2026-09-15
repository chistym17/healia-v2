from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from auth.supabase_auth import (
    get_current_user,
    login_email,
    refresh_session,
    signup_email,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/signup")
def signup(body: SignupRequest) -> dict[str, Any]:
    try:
        return signup_email(body.email, body.password, body.display_name)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login")
def login(body: LoginRequest) -> dict[str, Any]:
    try:
        return login_email(body.email, body.password)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/refresh")
def refresh(body: RefreshRequest) -> dict[str, Any]:
    try:
        return refresh_session(body.refresh_token)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/me")
def me(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return {"user": user}
