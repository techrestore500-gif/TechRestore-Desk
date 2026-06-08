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
                stop_time TEXT,
                recurrence TEXT,
                interval_minutes INTEGER,
                enabled INTEGER NOT NULL DEFAULT 1,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_triggered_at TEXT,
                original_text TEXT
            )
            """
        )

        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(market_notifications)").fetchall()
        }
        if "stop_time" not in columns:
            connection.execute("ALTER TABLE market_notifications ADD COLUMN stop_time TEXT")
        if "interval_minutes" not in columns:
            connection.execute("ALTER TABLE market_notifications ADD COLUMN interval_minutes INTEGER")

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS market_sms_allowlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT NOT NULL UNIQUE,
                label TEXT,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS market_sms_invite_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT NOT NULL,
                requested_label TEXT,
                message_text TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(phone_number, status)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS market_feedback_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT NOT NULL,
                feedback_text TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'sms',
                created_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_market_sms_allowlist_enabled
            ON market_sms_allowlist(phone_number, enabled)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_market_sms_invite_requests_status
            ON market_sms_invite_requests(status, updated_at)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_market_feedback_entries_created
            ON market_feedback_entries(created_at DESC, id DESC)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_market_notifications_recipient
            ON market_notifications(recipient_phone, enabled, completed, updated_at)
            """
        )

        connection.commit()
