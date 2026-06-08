from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from market_updates.storage import ensure_tables, get_connection

STATE_IDLE = "idle"


@dataclass(frozen=True)
class SmsSession:
    phone_number: str
    state: str
    draft: dict
    updated_at: str


def _now_iso() -> str:
    return datetime.now().isoformat()


def get_session(phone_number: str) -> SmsSession:
    ensure_tables()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT phone_number, state, draft_json, updated_at FROM market_sms_sessions WHERE phone_number = ?",
            (phone_number,),
        ).fetchone()

    if row is None:
        return SmsSession(phone_number=phone_number, state=STATE_IDLE, draft={}, updated_at=_now_iso())

    try:
        draft = json.loads(row["draft_json"])
    except json.JSONDecodeError:
        draft = {}

    if not isinstance(draft, dict):
        draft = {}

    return SmsSession(
        phone_number=row["phone_number"],
        state=row["state"],
        draft=draft,
        updated_at=row["updated_at"],
    )


def save_session(phone_number: str, *, state: str, draft: dict | None = None) -> SmsSession:
    ensure_tables()
    draft_payload = draft or {}
    updated_at = _now_iso()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO market_sms_sessions(phone_number, state, draft_json, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(phone_number)
            DO UPDATE SET
                state = excluded.state,
                draft_json = excluded.draft_json,
                updated_at = excluded.updated_at
            """,
            (phone_number, state, json.dumps(draft_payload), updated_at),
        )
        connection.commit()

    return SmsSession(phone_number=phone_number, state=state, draft=draft_payload, updated_at=updated_at)


def clear_session(phone_number: str) -> SmsSession:
    return save_session(phone_number, state=STATE_IDLE, draft={})
