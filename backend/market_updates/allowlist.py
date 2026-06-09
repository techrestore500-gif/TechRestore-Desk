from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any

from market_updates.storage import ensure_tables, get_connection


def _now_iso() -> str:
    return datetime.now().isoformat()


def normalize_phone(phone: str) -> str:
    compact = re.sub(r"[^0-9+]", "", (phone or "").strip())
    if compact.startswith("00"):
        compact = "+" + compact[2:]

    if compact.startswith("+"):
        digits = re.sub(r"\D", "", compact[1:])
        if len(digits) == 10:
            return "+1" + digits
        return ("+" + digits) if digits else ""

    digits = re.sub(r"\D", "", compact)
    if not digits:
        return ""
    if len(digits) == 10:
        return "+1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits
    return "+" + digits


def _match_candidates(phone_number: str) -> tuple[str, ...]:
    normalized = normalize_phone(phone_number)
    if not normalized:
        return ()

    candidates = {normalized}
    digits = re.sub(r"\D", "", normalized)

    # Backward compatibility for legacy records that were stored as +XXXXXXXXXX
    # instead of +1XXXXXXXXXX for US numbers.
    if len(digits) == 11 and digits.startswith("1"):
        candidates.add("+" + digits[1:])
    elif len(digits) == 10:
        candidates.add("+1" + digits)

    return tuple(candidates)


def _seed_from_env(connection) -> None:
    candidates: list[str] = []
    for key in ("MARKET_UPDATES_ALLOWED_NUMBERS", "MARKET_UPDATE_TO_NUMBERS", "MARKET_UPDATE_TO_NUMBER"):
        raw = os.getenv(key, "")
        if raw.strip():
            candidates.extend(raw.split(","))

    if not candidates:
        return

    now = _now_iso()
    for part in candidates:
        phone = normalize_phone(part)
        if not phone:
            continue
        connection.execute(
            """
            INSERT INTO market_sms_allowlist(phone_number, label, enabled, created_at, updated_at)
            VALUES (?, ?, 1, ?, ?)
            ON CONFLICT(phone_number) DO UPDATE SET enabled = 1, updated_at = excluded.updated_at
            """,
            (phone, "Env Seed", now, now),
        )


def is_number_allowed(phone_number: str) -> bool:
    ensure_tables()
    candidates = _match_candidates(phone_number)
    if not candidates:
        return False

    with get_connection() as connection:
        _seed_from_env(connection)
        placeholders = ", ".join("?" for _ in candidates)
        row = connection.execute(
            f"SELECT 1 FROM market_sms_allowlist WHERE phone_number IN ({placeholders}) AND enabled = 1 LIMIT 1",
            candidates,
        ).fetchone()
        connection.commit()
    return row is not None


def list_allowlist() -> list[dict[str, Any]]:
    ensure_tables()
    with get_connection() as connection:
        _seed_from_env(connection)
        rows = connection.execute(
            "SELECT * FROM market_sms_allowlist ORDER BY enabled DESC, updated_at DESC, id DESC"
        ).fetchall()
        connection.commit()
    return [dict(row) for row in rows]


def upsert_allowlist_number(phone_number: str, label: str | None = None, *, enabled: bool = True) -> dict[str, Any]:
    ensure_tables()
    normalized = normalize_phone(phone_number)
    if not normalized:
        raise ValueError("Invalid phone number")

    now = _now_iso()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO market_sms_allowlist(phone_number, label, enabled, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(phone_number) DO UPDATE SET
                label = COALESCE(excluded.label, market_sms_allowlist.label),
                enabled = excluded.enabled,
                updated_at = excluded.updated_at
            """,
            (normalized, (label or "").strip() or None, 1 if enabled else 0, now, now),
        )
        row = connection.execute(
            "SELECT * FROM market_sms_allowlist WHERE phone_number = ?",
            (normalized,),
        ).fetchone()
        connection.commit()
    return dict(row) if row is not None else {}


def disable_allowlist_number(phone_number: str) -> bool:
    ensure_tables()
    normalized = normalize_phone(phone_number)
    if not normalized:
        return False

    now = _now_iso()
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE market_sms_allowlist SET enabled = 0, updated_at = ? WHERE phone_number = ?",
            (now, normalized),
        )
        connection.commit()
        return cursor.rowcount > 0


def create_or_update_invite_request(phone_number: str, message_text: str | None = None, requested_label: str | None = None) -> dict[str, Any]:
    ensure_tables()
    normalized = normalize_phone(phone_number)
    if not normalized:
        raise ValueError("Invalid phone number")

    now = _now_iso()
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT * FROM market_sms_invite_requests WHERE phone_number = ? AND status = 'pending' LIMIT 1",
            (normalized,),
        ).fetchone()
        if existing is None:
            connection.execute(
                """
                INSERT INTO market_sms_invite_requests(phone_number, requested_label, message_text, status, created_at, updated_at)
                VALUES (?, ?, ?, 'pending', ?, ?)
                """,
                (normalized, (requested_label or "").strip() or None, (message_text or "").strip() or None, now, now),
            )
        else:
            connection.execute(
                """
                UPDATE market_sms_invite_requests
                SET requested_label = COALESCE(?, requested_label),
                    message_text = COALESCE(?, message_text),
                    updated_at = ?
                WHERE id = ?
                """,
                ((requested_label or "").strip() or None, (message_text or "").strip() or None, now, int(existing["id"])),
            )

        row = connection.execute(
            "SELECT * FROM market_sms_invite_requests WHERE phone_number = ? AND status = 'pending' LIMIT 1",
            (normalized,),
        ).fetchone()
        connection.commit()

    return dict(row) if row is not None else {}


def list_invite_requests(status: str = "pending") -> list[dict[str, Any]]:
    ensure_tables()
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM market_sms_invite_requests WHERE status = ? ORDER BY updated_at DESC, id DESC",
            (status,),
        ).fetchall()
    return [dict(row) for row in rows]


def approve_invite_request(request_id: int, label: str | None = None) -> dict[str, Any] | None:
    ensure_tables()
    now = _now_iso()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM market_sms_invite_requests WHERE id = ?",
            (request_id,),
        ).fetchone()
        if row is None:
            return None

        request_data = dict(row)
        if request_data.get("status") != "pending":
            return request_data

        phone = str(request_data.get("phone_number") or "")
        upsert_allowlist_number(phone, label=label or request_data.get("requested_label"), enabled=True)
        connection.execute(
            "UPDATE market_sms_invite_requests SET status = 'approved', updated_at = ? WHERE id = ?",
            (now, request_id),
        )
        updated = connection.execute(
            "SELECT * FROM market_sms_invite_requests WHERE id = ?",
            (request_id,),
        ).fetchone()
        connection.commit()

    return dict(updated) if updated is not None else None


def deny_invite_request(request_id: int) -> dict[str, Any] | None:
    ensure_tables()
    now = _now_iso()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM market_sms_invite_requests WHERE id = ?",
            (request_id,),
        ).fetchone()
        if row is None:
            return None
        connection.execute(
            "UPDATE market_sms_invite_requests SET status = 'denied', updated_at = ? WHERE id = ?",
            (now, request_id),
        )
        updated = connection.execute(
            "SELECT * FROM market_sms_invite_requests WHERE id = ?",
            (request_id,),
        ).fetchone()
        connection.commit()
    return dict(updated) if updated is not None else None
