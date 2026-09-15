from __future__ import annotations

from typing import Any

from db.connection import as_jsonb, fetch_all, fetch_one


def ensure_user(*, user_id: str, email: str, display_name: str | None = None) -> dict[str, Any]:
    row = fetch_one(
        """
        insert into public.users (id, email, display_name)
        values (%(id)s::uuid, %(email)s, %(display_name)s)
        on conflict (id) do update set
          email = excluded.email,
          display_name = coalesce(excluded.display_name, public.users.display_name),
          updated_at = now()
        returning id, email, display_name, created_at, updated_at
        """,
        {
            "id": user_id,
            "email": email,
            "display_name": display_name,
        },
    )
    assert row is not None
    return row


def get_user(user_id: str) -> dict[str, Any] | None:
    return fetch_one(
        """
        select id, email, display_name, created_at, updated_at
        from public.users
        where id = %(id)s::uuid
        """,
        {"id": user_id},
    )


def create_session(
    *,
    user_id: str,
    livekit_room_name: str | None = None,
    livekit_session_id: str | None = None,
    title: str | None = None,
    status: str = "started",
) -> dict[str, Any]:
    row = fetch_one(
        """
        insert into public.session_history (
          user_id, livekit_room_name, livekit_session_id, title, status
        )
        values (
          %(user_id)s::uuid, %(livekit_room_name)s, %(livekit_session_id)s,
          %(title)s, %(status)s
        )
        returning *
        """,
        {
            "user_id": user_id,
            "livekit_room_name": livekit_room_name,
            "livekit_session_id": livekit_session_id,
            "title": title,
            "status": status,
        },
    )
    assert row is not None
    return row


def list_sessions(user_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
    return fetch_all(
        """
        select
          sh.id,
          sh.user_id,
          sh.livekit_room_name,
          sh.livekit_session_id,
          sh.status,
          sh.title,
          sh.started_at,
          sh.completed_at,
          sh.created_at,
          sh.updated_at,
          (sr.id is not null) as has_results
        from public.session_history sh
        left join public.session_results sr on sr.session_id = sh.id
        where sh.user_id = %(user_id)s::uuid
        order by sh.started_at desc
        limit %(limit)s
        """,
        {"user_id": user_id, "limit": limit},
    )


def get_session(session_id: str, user_id: str) -> dict[str, Any] | None:
    return fetch_one(
        """
        select *
        from public.session_history
        where id = %(id)s::uuid and user_id = %(user_id)s::uuid
        """,
        {"id": session_id, "user_id": user_id},
    )


def update_session(
    session_id: str,
    user_id: str,
    *,
    status: str | None = None,
    title: str | None = None,
    transcript: list[dict[str, Any]] | None = None,
    livekit_room_name: str | None = None,
    livekit_session_id: str | None = None,
    completed: bool = False,
) -> dict[str, Any] | None:
    row = fetch_one(
        """
        update public.session_history set
          status = coalesce(%(status)s, status),
          title = coalesce(%(title)s, title),
          transcript = coalesce(%(transcript)s, transcript),
          livekit_room_name = coalesce(%(livekit_room_name)s, livekit_room_name),
          livekit_session_id = coalesce(%(livekit_session_id)s, livekit_session_id),
          completed_at = case
            when %(completed)s then coalesce(completed_at, now())
            else completed_at
          end,
          updated_at = now()
        where id = %(id)s::uuid and user_id = %(user_id)s::uuid
        returning *
        """,
        {
            "id": session_id,
            "user_id": user_id,
            "status": status,
            "title": title,
            "transcript": as_jsonb(transcript) if transcript is not None else None,
            "livekit_room_name": livekit_room_name,
            "livekit_session_id": livekit_session_id,
            "completed": completed,
        },
    )
    return row


def upsert_results(
    session_id: str,
    user_id: str,
    *,
    summary: str = "",
    possible_concerns: str = "",
    actions: list[Any] | None = None,
    warning_signs: str = "",
    seek_care: str = "",
    references: list[Any] | None = None,
    spoken_answer: str | None = None,
    confidence: str | None = None,
    raw_guidance: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    owned = get_session(session_id, user_id)
    if not owned:
        return None

    row = fetch_one(
        """
        insert into public.session_results (
          session_id, summary, possible_concerns, actions, warning_signs,
          seek_care, "references", spoken_answer, confidence, raw_guidance
        )
        values (
          %(session_id)s::uuid, %(summary)s, %(possible_concerns)s, %(actions)s,
          %(warning_signs)s, %(seek_care)s, %(references)s, %(spoken_answer)s,
          %(confidence)s, %(raw_guidance)s
        )
        on conflict (session_id) do update set
          summary = excluded.summary,
          possible_concerns = excluded.possible_concerns,
          actions = excluded.actions,
          warning_signs = excluded.warning_signs,
          seek_care = excluded.seek_care,
          "references" = excluded."references",
          spoken_answer = excluded.spoken_answer,
          confidence = excluded.confidence,
          raw_guidance = excluded.raw_guidance,
          updated_at = now()
        returning *
        """,
        {
            "session_id": session_id,
            "summary": summary,
            "possible_concerns": possible_concerns,
            "actions": as_jsonb(actions or []),
            "warning_signs": warning_signs,
            "seek_care": seek_care,
            "references": as_jsonb(references or []),
            "spoken_answer": spoken_answer,
            "confidence": confidence,
            "raw_guidance": as_jsonb(raw_guidance) if raw_guidance is not None else None,
        },
    )
    return row


def get_results(session_id: str, user_id: str) -> dict[str, Any] | None:
    return fetch_one(
        """
        select sr.*
        from public.session_results sr
        join public.session_history sh on sh.id = sr.session_id
        where sr.session_id = %(session_id)s::uuid
          and sh.user_id = %(user_id)s::uuid
        """,
        {"session_id": session_id, "user_id": user_id},
    )


def get_session_with_results(session_id: str, user_id: str) -> dict[str, Any] | None:
    session = get_session(session_id, user_id)
    if not session:
        return None
    results = get_results(session_id, user_id)
    return {"session": session, "results": results}


def delete_session(session_id: str, user_id: str) -> bool:
    row = fetch_one(
        """
        delete from public.session_history
        where id = %(id)s::uuid and user_id = %(user_id)s::uuid
        returning id
        """,
        {"id": session_id, "user_id": user_id},
    )
    return row is not None
