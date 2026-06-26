import sqlite3
import threading
from pathlib import Path

import pytest

import app.database as database


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    data_root = tmp_path / "var-data"
    backups_dir = data_root / "backups"
    db_path = data_root / "tech_restore_desk.sqlite"

    data_root.mkdir(parents=True, exist_ok=True)
    backups_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("TECH_RESTORE_APP_ENV", "development")
    monkeypatch.setenv("TECH_RESTORE_DATA_ROOT", str(data_root))
    monkeypatch.setattr(database, "PERSISTENT_DATA_ROOT", data_root)
    monkeypatch.setattr(database, "DATA_DIR", data_root)
    monkeypatch.setattr(database, "BACKUPS_DIR", backups_dir)
    monkeypatch.setattr(database, "DB_PATH", db_path)
    monkeypatch.setattr(database, "DEFAULT_DB_PATH", db_path)
    monkeypatch.setattr(database, "LEGACY_DB_PATH", db_path)
    monkeypatch.setattr(database, "SYSTEM_ACTIVITY_LOG_PATH", data_root / "system_activity_log.json")

    database.initialize_database()
    return {"data_root": data_root, "backups_dir": backups_dir, "db_path": db_path}


def _seed_representative_records() -> dict:
    with database.get_connection() as connection:
        now = database.utc_now()
        customer_id = connection.execute(
            """
            INSERT INTO customers (full_name, primary_phone, alternate_phone, email, notes, created_at, updated_at)
            VALUES (?, ?, NULL, NULL, ?, ?, ?)
            """,
            ("Backup Restore Customer", "555-8181", "backup restore test", now, now),
        ).lastrowid

        ticket_id = connection.execute(
            """
            INSERT INTO repair_tickets (
                ticket_number,
                customer_id,
                issue_category,
                water_damage_status,
                dropped_status,
                powers_on_status,
                charges_status,
                must_call_before_repair,
                customer_prefers_replacement_if_high,
                payment_status,
                status,
                priority,
                intake_date,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, 'unknown', 'unknown', 'unknown', 'unknown', 0, 0, 'partial', 'Needs Diagnosis', 'normal', ?, ?, ?)
            """,
            ("TR-BACKUP-RESTORE-001", customer_id, "Backup Restore Repair", now, now, now),
        ).lastrowid

        connection.execute(
            """
            INSERT INTO ticket_notes (ticket_id, note_type, body, created_by, created_at)
            VALUES (?, 'front_desk', 'Representative note', 'Backup Test', ?)
            """,
            (ticket_id, now),
        )

        connection.execute(
            """
            INSERT INTO ticket_status_history (ticket_id, old_status, new_status, changed_by, note, created_at)
            VALUES (?, 'New Intake', 'Needs Diagnosis', 'Backup Test', 'Representative status event', ?)
            """,
            (ticket_id, now),
        )

        connection.execute(
            """
            INSERT INTO activity_logs (user_id, entity_type, entity_id, action, old_value, new_value, request_id, created_at)
            VALUES (?, 'ticket', ?, 'backup_restore_seed', NULL, '{"seed":true}', 'req-backup-seed', ?)
            """,
            (1, ticket_id, now),
        )
        connection.commit()

    return {"customer_id": int(customer_id), "ticket_id": int(ticket_id)}


def test_backup_restore_verification_with_wal(isolated_db):
    ids = _seed_representative_records()

    with database.get_connection() as live_connection:
        live_customer_count = live_connection.execute("SELECT COUNT(*) AS total FROM customers").fetchone()["total"]
        live_ticket_count = live_connection.execute("SELECT COUNT(*) AS total FROM repair_tickets").fetchone()["total"]

    backup = database.create_database_backup(requested_by_user_id=7)
    backup_path = Path(backup["backup_path"])
    assert backup_path.exists()

    with sqlite3.connect(backup_path) as restore_connection:
        integrity = restore_connection.execute("PRAGMA integrity_check").fetchone()[0]
        restore_customer = restore_connection.execute(
            "SELECT id, full_name, primary_phone FROM customers WHERE id = ?",
            (ids["customer_id"],),
        ).fetchone()
        restore_ticket = restore_connection.execute(
            "SELECT id, ticket_number, status, payment_status FROM repair_tickets WHERE id = ?",
            (ids["ticket_id"],),
        ).fetchone()
        restore_note_count = restore_connection.execute(
            "SELECT COUNT(*) FROM ticket_notes WHERE ticket_id = ?",
            (ids["ticket_id"],),
        ).fetchone()[0]
        restore_history_count = restore_connection.execute(
            "SELECT COUNT(*) FROM ticket_status_history WHERE ticket_id = ?",
            (ids["ticket_id"],),
        ).fetchone()[0]

    assert str(integrity).lower() == "ok"
    assert restore_customer is not None
    assert restore_ticket is not None
    assert restore_note_count >= 1
    assert restore_history_count >= 1

    with database.get_connection() as live_connection:
        assert live_connection.execute("SELECT COUNT(*) AS total FROM customers").fetchone()["total"] == live_customer_count
        assert live_connection.execute("SELECT COUNT(*) AS total FROM repair_tickets").fetchone()["total"] == live_ticket_count


def test_concurrent_wal_backup_produces_valid_snapshot(isolated_db):
    _seed_representative_records()

    stop = {"done": False}

    def _writer():
        index = 0
        while not stop["done"] and index < 25:
            with database.get_connection() as connection:
                now = database.utc_now()
                connection.execute(
                    """
                    INSERT INTO customers (full_name, primary_phone, alternate_phone, email, notes, created_at, updated_at)
                    VALUES (?, ?, NULL, NULL, NULL, ?, ?)
                    """,
                    (f"Concurrent Customer {index}", f"555-91{index:02d}", now, now),
                )
                connection.commit()
            index += 1

    writer = threading.Thread(target=_writer)
    writer.start()
    backup = database.create_database_backup(requested_by_user_id=2)
    stop["done"] = True
    writer.join(timeout=5)

    with sqlite3.connect(backup["backup_path"]) as restore_connection:
        integrity = restore_connection.execute("PRAGMA integrity_check").fetchone()[0]
    assert str(integrity).lower() == "ok"


def test_backup_retention_keeps_newest_backups(isolated_db, monkeypatch):
    monkeypatch.setenv("TECH_RESTORE_BACKUP_RETENTION_COUNT", "2")

    first = database.create_database_backup(requested_by_user_id=3)
    second = database.create_database_backup(requested_by_user_id=3)
    third = database.create_database_backup(requested_by_user_id=3)

    existing = sorted(database.BACKUPS_DIR.glob("backup-*.sqlite"))
    names = {path.name for path in existing}

    assert len(existing) <= 2
    assert Path(second["backup_path"]).name in names or Path(first["backup_path"]).name in names
    assert Path(third["backup_path"]).name in names


def test_backup_integrity_failure_removes_invalid_backup_and_keeps_live_db(isolated_db, monkeypatch):
    _seed_representative_records()

    with database.get_connection() as connection:
        before_count = connection.execute("SELECT COUNT(*) AS total FROM customers").fetchone()["total"]

    monkeypatch.setattr(database, "_verify_sqlite_integrity", lambda _path: (False, "simulated-failure"))

    with pytest.raises(RuntimeError):
        database.create_database_backup(requested_by_user_id=4)

    assert len(list(database.BACKUPS_DIR.glob("backup-*.sqlite"))) == 0

    with database.get_connection() as connection:
        after_count = connection.execute("SELECT COUNT(*) AS total FROM customers").fetchone()["total"]

    assert after_count == before_count


def test_backup_filenames_are_unique(isolated_db):
    first = database.create_database_backup(requested_by_user_id=5)
    second = database.create_database_backup(requested_by_user_id=5)

    assert first["file_name"] != second["file_name"]
    assert Path(first["backup_path"]).exists()
    assert Path(second["backup_path"]).exists()
