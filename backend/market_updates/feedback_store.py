from __future__ import annotations

from datetime import datetime
import logging
import os
from typing import Any

import requests

from market_updates.allowlist import normalize_phone
from market_updates.storage import ensure_tables, get_connection

logger = logging.getLogger(__name__)


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

    _forward_feedback_to_portal(normalized, text, source.strip() or "sms")

    return dict(row) if row is not None else {}


def _forward_feedback_to_portal(phone_number: str, feedback_text: str, source: str) -> None:
    ingest_url = os.getenv("FEEDBACK_PORTAL_INGEST_URL", "").strip()
    if not ingest_url:
        return

    token = os.getenv("FEEDBACK_PORTAL_INGEST_TOKEN", "").strip()
    headers: dict[str, str] = {}
    if token:
        headers["X-Feedback-Token"] = token

    try:
        requests.post(
            ingest_url,
            data={
                "phone_number": phone_number,
                "feedback_text": feedback_text,
                "source": source,
            },
            headers=headers,
            timeout=8,
        )
    except Exception:
        logger.exception("Failed forwarding feedback entry to portal ingest endpoint")


def list_feedback_entries(limit: int = 200) -> list[dict[str, Any]]:
    ensure_tables()
    safe_limit = max(1, min(limit, 1000))
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM market_feedback_entries ORDER BY created_at DESC, id DESC LIMIT ?",
            (safe_limit,),
        ).fetchall()
    return [dict(row) for row in rows]
