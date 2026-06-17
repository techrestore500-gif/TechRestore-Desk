from __future__ import annotations

from pathlib import Path

import pytest

import app.database as database
from app.repositories.auth import AuthRepository
from scripts.seed_real_tech_restore_data import run_real_data_reset_import


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    test_db_path = tmp_path / "tech_restore_real_seed_test.sqlite"
    test_backups_dir = tmp_path / "backups"
    test_backups_dir.mkdir()
    test_activity_log_path = tmp_path / "system_activity_log.json"

    monkeypatch.setattr(database, "DB_PATH", test_db_path)
    monkeypatch.setattr(database, "DEFAULT_DB_PATH", test_db_path)
    monkeypatch.setattr(database, "LEGACY_DB_PATH", test_db_path)
    monkeypatch.setattr(database, "BACKUPS_DIR", test_backups_dir)
    monkeypatch.setattr(database, "SYSTEM_ACTIVITY_LOG_PATH", test_activity_log_path)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path.as_posix()}")

    database.initialize_database()
    AuthRepository.ensure_user_table()
    AuthRepository.create_user(
        name="Owner User",
        email="owner@example.com",
        username="owneruser",
        password_hash="hashed",
        role="owner",
        status="active",
        approved_by=None,
    )

    with database.get_connection() as connection:
        connection.execute(
            """
            INSERT INTO twilio_settings (
                id,
                account_sid,
                auth_token_ciphertext,
                phone_number,
                public_webhook_base_url,
                voicemail_greeting,
                voicemail_greeting_audio_url,
                created_at,
                updated_at
            ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                account_sid = excluded.account_sid,
                auth_token_ciphertext = excluded.auth_token_ciphertext,
                phone_number = excluded.phone_number,
                public_webhook_base_url = excluded.public_webhook_base_url,
                voicemail_greeting = excluded.voicemail_greeting,
                voicemail_greeting_audio_url = excluded.voicemail_greeting_audio_url,
                updated_at = excluded.updated_at
            """,
            (
                "sid",
                "cipher",
                "+17320000000",
                "https://example.com",
                "Hello",
                None,
                "2026-06-02T00:00:00+00:00",
                "2026-06-02T00:00:00+00:00",
            ),
        )
        connection.commit()

    return test_db_path


def test_real_data_seed_script_replaces_demo_ticket_and_hours_data_without_touching_protected_tables(test_db):
    summary = run_real_data_reset_import()
    second_summary = run_real_data_reset_import()

    assert Path(summary.backup_path).exists()
    assert Path(second_summary.backup_path).exists()
    assert "inserted inventory purchase note" in summary.inventory_notes_result or "updated inventory purchase note" in summary.inventory_notes_result

    with database.get_connection() as connection:
        customer_count = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        ticket_count = connection.execute("SELECT COUNT(*) FROM repair_tickets").fetchone()[0]
        distinct_ticket_numbers = connection.execute("SELECT COUNT(DISTINCT ticket_number) FROM repair_tickets").fetchone()[0]
        hours_count = connection.execute("SELECT COUNT(*) FROM technician_hours").fetchone()[0]
        users_count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        twilio_count = connection.execute("SELECT COUNT(*) FROM twilio_settings").fetchone()[0]
        pricing_defaults_count = connection.execute("SELECT COUNT(*) FROM pricing_defaults").fetchone()[0]
        workflow_rules_count = connection.execute("SELECT COUNT(*) FROM status_workflow_rules").fetchone()[0]
        purchase = connection.execute(
            "SELECT reference_number, total_cost FROM inventory_purchases WHERE reference_number = ?",
            ("TR-REAL-STOCK-20260513",),
        ).fetchone()
        purchase_items_count = connection.execute(
            "SELECT COUNT(*) FROM inventory_purchase_items WHERE purchase_id = (SELECT id FROM inventory_purchases WHERE reference_number = ?)",
            ("TR-REAL-STOCK-20260513",),
        ).fetchone()[0]
        legacy_ticket_number_count = connection.execute(
            "SELECT COUNT(*) FROM repair_tickets WHERE ticket_number LIKE 'TR-REAL-%'"
        ).fetchone()[0]

        yossi_weiss = connection.execute(
            """
            SELECT rt.device_model_text_override, rt.final_price, rt.payment_status, rt.status
            FROM repair_tickets rt
            JOIN customers c ON c.id = rt.customer_id
            WHERE c.full_name = 'Yossi Weiss'
            ORDER BY rt.id ASC
            """
        ).fetchall()
        yossi_toder = connection.execute(
            """
            SELECT c.primary_phone, rt.final_price, rt.status
            FROM repair_tickets rt
            JOIN customers c ON c.id = rt.customer_id
            WHERE c.full_name = 'Yossi Toder'
            LIMIT 1
            """
        ).fetchone()
        ungar = connection.execute(
            """
            SELECT rt.final_price, rt.payment_status, rt.status
            FROM repair_tickets rt
            JOIN customers c ON c.id = rt.customer_id
            WHERE c.full_name = 'Ungar'
            LIMIT 1
            """
        ).fetchone()
        unknown_screen = connection.execute(
            """
            SELECT c.primary_phone, rt.device_model_text_override, rt.status
            FROM repair_tickets rt
            JOIN customers c ON c.id = rt.customer_id
            WHERE c.full_name = 'Unknown Screen Customer'
            LIMIT 1
            """
        ).fetchone()
        miriam_drew = connection.execute(
            """
            SELECT rt.payment_status, rt.status
            FROM repair_tickets rt
            JOIN customers c ON c.id = rt.customer_id
            WHERE c.full_name = 'Miriam Drew'
            LIMIT 1
            """
        ).fetchone()
        globerman = connection.execute(
            """
            SELECT rt.payment_status, rt.status
            FROM repair_tickets rt
            JOIN customers c ON c.id = rt.customer_id
            WHERE c.full_name = 'Globerman'
            LIMIT 1
            """
        ).fetchone()
        miriam_braun = connection.execute(
            """
            SELECT rt.payment_status, rt.final_price, rt.status
            FROM repair_tickets rt
            JOIN customers c ON c.id = rt.customer_id
            WHERE c.full_name = 'Miriam Braun'
            LIMIT 1
            """
        ).fetchone()
        dorpman = connection.execute(
            """
            SELECT rt.payment_status, rt.final_price, rt.status
            FROM repair_tickets rt
            JOIN customers c ON c.id = rt.customer_id
            WHERE c.full_name = 'Dorfman'
            LIMIT 1
            """
        ).fetchone()
        walk_in = connection.execute(
            """
            SELECT rt.payment_status, rt.final_price, rt.status, c.primary_phone
            FROM repair_tickets rt
            JOIN customers c ON c.id = rt.customer_id
            WHERE c.full_name = 'Unknown / walk-in'
            LIMIT 1
            """
        ).fetchone()
        confirmed_unpaid_jobs = connection.execute(
            """
            SELECT COUNT(*)
            FROM repair_tickets rt
            JOIN customers c ON c.id = rt.customer_id
            WHERE c.full_name = 'Yossi Weiss'
              AND rt.status = 'Picked Up / Closed'
              AND rt.payment_status = 'unpaid'
              AND COALESCE(rt.final_price, 0) = 25.0
            """
        ).fetchone()[0]

    assert customer_count == 9
    assert ticket_count == 11
    assert distinct_ticket_numbers == 11
    assert legacy_ticket_number_count == 0
    assert hours_count == 0
    assert users_count == 1
    assert twilio_count == 1
    assert pricing_defaults_count > 0
    assert workflow_rules_count > 0
    assert purchase is not None
    assert purchase["reference_number"] == "TR-REAL-STOCK-20260513"
    assert purchase["total_cost"] == 770.0
    assert purchase_items_count == 3
    assert len(yossi_weiss) == 3
    assert confirmed_unpaid_jobs == 2
    assert any(row["status"] == "In Repair" and row["payment_status"] == "unpaid" and row["final_price"] is None for row in yossi_weiss)
    assert yossi_toder["primary_phone"] == "732-664-1835"
    assert yossi_toder["final_price"] == 0.0
    assert yossi_toder["status"] == "Customer Declined"
    assert ungar["final_price"] == 0.0
    assert ungar["payment_status"] == "paid"
    assert ungar["status"] == "Picked Up / Closed"
    assert unknown_screen["primary_phone"] == "732-237-4070"
    assert "Samsung Galaxy A13 5G / SM-A136U1" in unknown_screen["device_model_text_override"]
    assert unknown_screen["status"] == "Customer Declined"
    assert miriam_drew["payment_status"] == "paid"
    assert miriam_drew["status"] == "Picked Up / Closed"
    assert globerman["payment_status"] == "paid"
    assert globerman["status"] == "Picked Up / Closed"
    assert miriam_braun["payment_status"] == "unpaid"
    assert miriam_braun["status"] == "Waiting for Parts"
    assert miriam_braun["final_price"] is None
    assert dorpman["payment_status"] == "unpaid"
    assert dorpman["status"] == "New Intake"
    assert dorpman["final_price"] is None
    assert walk_in["payment_status"] == "paid"
    assert walk_in["status"] == "Picked Up / Closed"
    assert walk_in["primary_phone"] is None