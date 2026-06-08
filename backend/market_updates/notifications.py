from __future__ import annotations

from datetime import datetime
from typing import Any

from market_updates.storage import ensure_tables, get_connection


def _now_iso() -> str:
    return datetime.now().isoformat()


def create_notification(
    *,
    recipient_phone: str,
    notification_type: str,
    symbol: str | None,
    display_name: str | None,
    condition: str | None,
    threshold: float | None,
    reminder_time: str | None,
    recurrence: str | None,
    original_text: str,
) -> dict[str, Any]:
    ensure_tables()

    # Simple duplicate guard for active notifications with same key fields.
    with get_connection() as connection:
        duplicate = connection.execute(
            """
            SELECT id FROM market_notifications
            WHERE recipient_phone = ?
              AND type = ?
              AND COALESCE(symbol, '') = COALESCE(?, '')
              AND COALESCE(condition, '') = COALESCE(?, '')
              AND COALESCE(threshold, -1) = COALESCE(?, -1)
              AND COALESCE(reminder_time, '') = COALESCE(?, '')
              AND enabled = 1
              AND completed = 0
            """,
            (
                recipient_phone,
                notification_type,
                symbol,
                condition,
                threshold,
                reminder_time,
            ),
        ).fetchone()
        if duplicate is not None:
            return get_notification_by_id(int(duplicate["id"])) or {}

        now = _now_iso()
        cursor = connection.execute(
            """
            INSERT INTO market_notifications(
                recipient_phone, type, symbol, display_name, condition, threshold,
                reminder_time, recurrence, enabled, completed, created_at, updated_at,
                last_triggered_at, original_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?, ?, NULL, ?)
            """,
            (
                recipient_phone,
                notification_type,
                symbol,
                display_name,
                condition,
                threshold,
                reminder_time,
                recurrence,
                now,
                now,
                original_text,
            ),
        )
        connection.commit()
        notification_id = int(cursor.lastrowid)

    return get_notification_by_id(notification_id) or {}


def get_notification_by_id(notification_id: int) -> dict[str, Any] | None:
    ensure_tables()
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM market_notifications WHERE id = ?", (notification_id,)).fetchone()
    return dict(row) if row is not None else None


def list_notifications_for_recipient(recipient_phone: str) -> list[dict[str, Any]]:
    ensure_tables()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM market_notifications
            WHERE recipient_phone = ?
              AND completed = 0
            ORDER BY id ASC
            """,
            (recipient_phone,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_notification_by_index(recipient_phone: str, index_1_based: int) -> dict[str, Any] | None:
    if index_1_based < 1:
        return None
    notifications = list_notifications_for_recipient(recipient_phone)
    if index_1_based > len(notifications):
        return None
    return notifications[index_1_based - 1]


def delete_notification_for_recipient(recipient_phone: str, notification_id: int) -> bool:
    ensure_tables()
    now = _now_iso()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE market_notifications
            SET completed = 1, enabled = 0, updated_at = ?
            WHERE id = ? AND recipient_phone = ?
            """,
            (now, notification_id, recipient_phone),
        )
        connection.commit()
        return cursor.rowcount > 0


def set_notification_enabled_for_recipient(recipient_phone: str, notification_id: int, enabled: bool) -> bool:
    ensure_tables()
    now = _now_iso()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE market_notifications
            SET enabled = ?, updated_at = ?
            WHERE id = ? AND recipient_phone = ? AND completed = 0
            """,
            (1 if enabled else 0, now, notification_id, recipient_phone),
        )
        connection.commit()
        return cursor.rowcount > 0


def build_summary(notification: dict[str, Any]) -> str:
    notification_type = notification.get("type")
    display_name = notification.get("display_name") or notification.get("symbol") or "Market"

    if notification_type == "price_alert":
        direction = str(notification.get("condition") or "").lower()
        threshold = notification.get("threshold")
        if threshold is None:
            return f"{display_name} price alert"
        direction_word = "below" if direction == "below" else "above"
        return f"{display_name} {direction_word} ${threshold:,.2f}"

    if notification_type == "one_time_reminder":
        return f"One-time update at {notification.get('reminder_time')}"

    if notification_type == "daily_reminder":
        return f"Daily update at {notification.get('reminder_time')}"

    return "Notification"


def mark_notification_triggered(notification_id: int, *, complete: bool) -> None:
    ensure_tables()
    now = _now_iso()
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE market_notifications
            SET last_triggered_at = ?, updated_at = ?, completed = ?, enabled = ?
            WHERE id = ?
            """,
            (now, now, 1 if complete else 0, 0 if complete else 1, notification_id),
        )
        connection.commit()


def update_last_triggered(notification_id: int) -> None:
    ensure_tables()
    now = _now_iso()
    with get_connection() as connection:
        connection.execute(
            "UPDATE market_notifications SET last_triggered_at = ?, updated_at = ? WHERE id = ?",
            (now, now, notification_id),
        )
        connection.commit()


def list_due_notifications() -> list[dict[str, Any]]:
    ensure_tables()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM market_notifications
            WHERE enabled = 1 AND completed = 0
            ORDER BY id ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]
