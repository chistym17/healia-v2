"""LiveKit connection token API for the frontend."""

import os
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from google.protobuf.json_format import ParseDict
from livekit import api
from livekit.protocol.room import RoomConfiguration
from pydantic import BaseModel, ConfigDict, Field

from auth.supabase_auth import get_current_user
from security.rate_limit import limit_user

# Must match livekit_agent.config.AGENT_NAME
DEFAULT_AGENT_NAME = "healia"

router = APIRouter(prefix="/api/livekit", tags=["LiveKit"])


class TokenRequest(BaseModel):
    """Accepts LiveKit TokenSource camelCase and snake_case bodies."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    room_name: str | None = Field(default=None, alias="roomName")
    participant_identity: str | None = Field(default=None, alias="participantIdentity")
    participant_name: str = Field(
        default="Patient", max_length=100, alias="participantName"
    )
    room_config: dict[str, Any] | None = Field(default=None, alias="roomConfig")


class TokenResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    server_url: str = Field(alias="serverUrl")
    participant_token: str = Field(alias="participantToken")


def _ensure_agent_dispatch(room_config: dict[str, Any] | None) -> dict[str, Any]:
    """Named worker (agent_name=healia) only joins when explicitly dispatched."""
    cfg: dict[str, Any] = dict(room_config or {})
    agents = cfg.get("agents") or cfg.get("Agents") or []
    if not isinstance(agents, list):
        agents = []
    agents = list(agents)
    if not agents:
        agents = [{"agent_name": DEFAULT_AGENT_NAME}]
    else:
        # Normalize first agent name if missing
        first = dict(agents[0] or {})
        if not (first.get("agent_name") or first.get("agentName")):
            first["agent_name"] = DEFAULT_AGENT_NAME
        agents[0] = first
    cfg["agents"] = agents
    return cfg


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

    room_config = _ensure_agent_dispatch(request.room_config)
    token = token.with_room_config(ParseDict(room_config, RoomConfiguration()))

    return TokenResponse(
        server_url=livekit_url,
        participant_token=token.to_jwt(),
    )
