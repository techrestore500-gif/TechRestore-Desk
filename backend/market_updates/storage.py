from __future__ import annotations

import os
import sqlite3
from pathlib import Path


def _default_db_path() -> Path:
    # Keep market assistant state isolated from the main app schema.
    return Path(__file__).resolve().parent.parent / "data" / "market_updates.sqlite"


def get_db_path() -> Path:
    raw = os.getenv("MARKET_UPDATES_DB_PATH")
    if raw and raw.strip():
        return Path(raw.strip()).resolve()
    return _default_db_path()


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    return connection


def ensure_tables() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS market_sms_sessions (
                phone_number TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                draft_json TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS market_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_phone TEXT NOT NULL,
                type TEXT NOT NULL,
                symbol TEXT,
                display_name TEXT,
                condition TEXT,
                threshold REAL,
                reminder_time TEXT,
                recurrence TEXT,
                enabled INTEGER NOT NULL DEFAULT 1,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_triggered_at TEXT,
                original_text TEXT
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_market_notifications_recipient
            ON market_notifications(recipient_phone, enabled, completed, updated_at)
            """
        )

        connection.commit()
