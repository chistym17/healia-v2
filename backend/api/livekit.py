"""LiveKit connection token API for the frontend."""

import os
import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from google.protobuf.json_format import ParseDict
from livekit import api
from livekit.protocol.room import RoomConfiguration
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/livekit", tags=["LiveKit"])


class TokenRequest(BaseModel):
    room_name: str | None = None
    participant_identity: str | None = None
    participant_name: str = Field(default="Patient", max_length=100)
    # LiveKit frontend TokenSource sends this when agentName is set.
    room_config: dict[str, Any] | None = None


class TokenResponse(BaseModel):
    server_url: str
    participant_token: str


@router.post("/token", response_model=TokenResponse, status_code=201)
async def create_livekit_token(request: TokenRequest) -> TokenResponse:
    livekit_url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not livekit_url or not api_key or not api_secret:
        raise HTTPException(
            status_code=500,
            detail="LiveKit environment variables are missing.",
        )

    room_name = request.room_name or f"consult-{uuid.uuid4().hex[:12]}"
    participant_identity = (
        request.participant_identity
        or f"patient-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    )

    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity(participant_identity)
        .with_name(request.participant_name)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            )
        )
    )

    # Frontend sends a JSON dict; AccessToken expects a protobuf RoomConfiguration.
    if request.room_config:
        room_config = ParseDict(request.room_config, RoomConfiguration())
        token = token.with_room_config(room_config)

    return TokenResponse(
        server_url=livekit_url,
        participant_token=token.to_jwt(),
    )
