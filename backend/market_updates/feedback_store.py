from __future__ import annotations

from datetime import datetime
from typing import Any

from market_updates.allowlist import normalize_phone
from market_updates.storage import ensure_tables, get_connection


def _now_iso() -> str:
    return datetime.now().isoformat()


def create_feedback_entry(phone_number: str, feedback_text: str, source: str = "sms") -> dict[str, Any]:
    ensure_tables()
    normalized = normalize_phone(phone_number)
    text = (feedback_text or "").strip()
    if not normalized:
        raise ValueError("Invalid phone number")
    if not text:
        raise ValueError("Feedback text is required")

    now = _now_iso()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO market_feedback_entries(phone_number, feedback_text, source, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (normalized, text, source.strip() or "sms", now),
        )
        row = connection.execute(
            "SELECT * FROM market_feedback_entries WHERE id = ?",
            (int(cursor.lastrowid),),
        ).fetchone()
        connection.commit()

    return dict(row) if row is not None else {}


def list_feedback_entries(limit: int = 200) -> list[dict[str, Any]]:
    ensure_tables()
    safe_limit = max(1, min(limit, 1000))
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM market_feedback_entries ORDER BY created_at DESC, id DESC LIMIT ?",
            (safe_limit,),
        ).fetchall()
    return [dict(row) for row in rows]
