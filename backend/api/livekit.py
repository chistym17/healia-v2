"""LiveKit connection token API for the frontend."""

import os
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from google.protobuf.json_format import ParseDict
from livekit import api
from livekit.protocol.room import RoomConfiguration
from pydantic import BaseModel, Field

from auth.supabase_auth import get_current_user
from security.rate_limit import limit_user

router = APIRouter(prefix="/api/livekit", tags=["LiveKit"])


class TokenRequest(BaseModel):
    room_name: str | None = None
    participant_identity: str | None = None
    participant_name: str = Field(default="Patient", max_length=100)
    room_config: dict[str, Any] | None = None


class TokenResponse(BaseModel):
    server_url: str
    participant_token: str


@router.post("/token", response_model=TokenResponse, status_code=201)
async def create_livekit_token(
    request: TokenRequest,
    user: dict[str, Any] = Depends(get_current_user),
    _: None = Depends(limit_user("livekit_token", 5, 60.0)),
) -> TokenResponse:
    livekit_url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not livekit_url or not api_key or not api_secret:
        raise HTTPException(
            status_code=500,
            detail="LiveKit environment variables are missing.",
        )

    room_name = request.room_name or f"consult-{uuid.uuid4().hex[:12]}"
    # Prefer stable identity tied to the authenticated user.
    participant_identity = (
        request.participant_identity
        or f"user-{user['id'][:8]}-{int(time.time())}-{uuid.uuid4().hex[:4]}"
    )
    participant_name = (
        user.get("display_name")
        or user.get("email")
        or request.participant_name
        or "Patient"
    )

    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity(participant_identity)
        .with_name(str(participant_name)[:100])
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            )
        )
    )

    if request.room_config:
        room_config = ParseDict(request.room_config, RoomConfiguration())
        token = token.with_room_config(room_config)

    return TokenResponse(
        server_url=livekit_url,
        participant_token=token.to_jwt(),
    )
