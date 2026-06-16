from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from cryptography.fernet import Fernet, InvalidToken

from app.core.query_metrics import query_metrics_registry
from app.core.request_context import get_request_id
from app.seed import REPAIR_CATEGORIES, SUPPORTED_DEVICE_MODELS


APP_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = APP_ROOT / "data"
BACKUPS_DIR = APP_ROOT / "backups"
SYSTEM_ACTIVITY_LOG_PATH = DATA_DIR / "system_activity_log.json"
LEGACY_DB_PATH = DATA_DIR / "repairdesk.sqlite"


def _resolve_db_path_from_env() -> Path | None:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        return None

    if database_url.startswith("sqlite:///"):
        raw_path = database_url[len("sqlite:///") :]
        if raw_path.startswith("/") and len(raw_path) > 2 and raw_path[2] == ":":
            # Normalize sqlite URLs like sqlite:////C:/path/to/db.sqlite used on Windows.
            raw_path = raw_path[1:]
        return Path(raw_path).expanduser().resolve()

    return Path(database_url).expanduser().resolve()


DEFAULT_DB_PATH = DATA_DIR / "tech_restore_desk.sqlite"
ENV_DB_PATH = _resolve_db_path_from_env()
DB_PATH = ENV_DB_PATH or (DEFAULT_DB_PATH if DEFAULT_DB_PATH.exists() or not LEGACY_DB_PATH.exists() else LEGACY_DB_PATH)
SLOW_QUERY_THRESHOLD_MS = float(os.getenv("TECH_RESTORE_SLOW_QUERY_MS", "120"))
logger = logging.getLogger(__name__)


def _record_query(sql: str, duration_ms: float) -> None:
    request_id = get_request_id()
    query_metrics_registry.record(
        sql=sql,
        duration_ms=duration_ms,
        request_id=request_id,
        slow_threshold_ms=SLOW_QUERY_THRESHOLD_MS,
    )
    if duration_ms >= SLOW_QUERY_THRESHOLD_MS:
        logger.warning(
            "Slow SQL query",
            extra={
                "action": "slow_query",
                "request_id": request_id,
                "duration_ms": round(duration_ms, 3),
                "entity_type": "database",
                "entity_id": None,
            },
        )


class InstrumentedConnection(sqlite3.Connection):
    def execute(self, sql, parameters=(), /):
        start = perf_counter()
        try:
            return super().execute(sql, parameters)
        finally:
            _record_query(str(sql), (perf_counter() - start) * 1000)

    def executemany(self, sql, seq_of_parameters, /):
        start = perf_counter()
        try:
            return super().executemany(sql, seq_of_parameters)
        finally:
            _record_query(str(sql), (perf_counter() - start) * 1000)

    def executescript(self, sql_script, /):
        start = perf_counter()
        try:
            return super().executescript(sql_script)
        finally:
            _record_query(str(sql_script), (perf_counter() - start) * 1000)


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, factory=InstrumentedConnection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")
    return connection


def create_database_backup() -> dict:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    created_at = utc_now()
    timestamp = created_at.replace(":", "-")
    file_name = f"backup-{timestamp}.sqlite"
    backup_path = BACKUPS_DIR / file_name
    shutil.copy2(DB_PATH, backup_path)
    file_size_bytes = backup_path.stat().st_size
    record_system_activity(
        activity_type="backup",
        file_name=file_name,
        file_size_bytes=file_size_bytes,
        file_path=str(backup_path),
        created_at=created_at,
    )
    return {
        "file_name": file_name,
        "backup_path": str(backup_path),
        "created_at": created_at,
        "file_size_bytes": file_size_bytes,
    }


def export_database_snapshot() -> tuple[str, bytes]:
    created_at = utc_now()
    export_timestamp = created_at.replace(":", "-")
    file_name = f"tech-restore-export-{export_timestamp}.json"

    with get_connection() as connection:
        table_rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name ASC
            """
        ).fetchall()

        snapshot = {
            "exported_at": utc_now(),
            "database_path": str(DB_PATH),
            "tables": {},
        }

        for row in table_rows:
            table_name = row["name"]
            table_data = connection.execute(f"SELECT * FROM {table_name}").fetchall()
            snapshot["tables"][table_name] = [dict(item) for item in table_data]

    payload = json.dumps(snapshot, indent=2).encode("utf-8")
    record_system_activity(
        activity_type="export",
        file_name=file_name,
        file_size_bytes=len(payload),
        file_path=None,
        created_at=created_at,
    )
    return file_name, payload


def _read_system_activity_log() -> list[dict]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SYSTEM_ACTIVITY_LOG_PATH.exists():
        return []

    try:
        payload = json.loads(SYSTEM_ACTIVITY_LOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    return payload if isinstance(payload, list) else []


def _write_system_activity_log(items: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SYSTEM_ACTIVITY_LOG_PATH.write_text(json.dumps(items[:25], indent=2), encoding="utf-8")


def record_system_activity(
    activity_type: str,
    file_name: str,
    file_size_bytes: int,
    file_path: str | None,
    created_at: str | None = None,
) -> dict:
    activity = {
        "activity_type": activity_type,
        "file_name": file_name,
        "file_size_bytes": file_size_bytes,
        "file_path": file_path,
        "created_at": created_at or utc_now(),
    }
    items = _read_system_activity_log()
    items.insert(0, activity)
    _write_system_activity_log(items)
    return activity


def list_system_activity(limit: int = 10) -> list[dict]:
    return _read_system_activity_log()[:limit]


def _table_has_column(connection: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row["name"] == column_name for row in rows)


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                primary_phone TEXT,
                alternate_phone TEXT,
                email TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS supported_device_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manufacturer TEXT,
                device_family TEXT NOT NULL,
                model_name TEXT NOT NULL,
                model_aliases TEXT,
                repair_policy TEXT NOT NULL,
                notes TEXT,
                active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS repair_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_number TEXT NOT NULL UNIQUE,
                customer_id INTEGER NOT NULL,
                device_model_id INTEGER,
                device_model_text_override TEXT,
                carrier TEXT,
                sim_type TEXT,
                imei_serial TEXT,
                device_color TEXT,
                filter_status TEXT,
                issue_category TEXT NOT NULL,
                issue_description TEXT,
                condition_summary TEXT,
                water_damage_status TEXT NOT NULL DEFAULT 'unknown',
                dropped_status TEXT NOT NULL DEFAULT 'unknown',
                powers_on_status TEXT NOT NULL DEFAULT 'unknown',
                charges_status TEXT NOT NULL DEFAULT 'unknown',
                customer_approval_limit REAL,
                must_call_before_repair INTEGER NOT NULL DEFAULT 0,
                customer_prefers_replacement_if_high INTEGER NOT NULL DEFAULT 0,
                estimated_price REAL,
                final_price REAL,
                payment_status TEXT NOT NULL DEFAULT 'unpaid',
                diagnostic_fee REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'New Intake',
                priority TEXT NOT NULL DEFAULT 'normal',
                intake_staff TEXT,
                assigned_technician TEXT,
                intake_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (device_model_id) REFERENCES supported_device_models(id)
            )
            """
        )
        if not _table_has_column(connection, "repair_tickets", "payment_status"):
            connection.execute(
                "ALTER TABLE repair_tickets ADD COLUMN payment_status TEXT NOT NULL DEFAULT 'unpaid'"
            )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                old_status TEXT,
                new_status TEXT NOT NULL,
                changed_by TEXT,
                note TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES repair_tickets(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                note_type TEXT NOT NULL,
                body TEXT NOT NULL,
                created_by TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES repair_tickets(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS repair_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                repair_category_id INTEGER,
                action_description TEXT,
                part_cost REAL NOT NULL DEFAULT 0,
                labor_minutes INTEGER NOT NULL DEFAULT 0,
                difficulty_level INTEGER NOT NULL DEFAULT 1,
                risk_level INTEGER NOT NULL DEFAULT 1,
                calculated_price REAL,
                final_price REAL,
                status TEXT NOT NULL DEFAULT 'planned',
                performed_by TEXT,
                performed_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES repair_tickets(id),
                FOREIGN KEY (repair_category_id) REFERENCES repair_categories(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS loaner_phones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                loaner_code TEXT NOT NULL UNIQUE,
                manufacturer TEXT,
                model TEXT NOT NULL,
                carrier_compatibility TEXT,
                charger_type TEXT,
                sim_type TEXT,
                filter_status TEXT,
                condition_current TEXT,
                status TEXT NOT NULL DEFAULT 'Available',
                default_deposit REAL NOT NULL DEFAULT 0,
                notes TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS loaner_checkouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                loaner_phone_id INTEGER NOT NULL,
                ticket_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,
                date_out TEXT NOT NULL,
                expected_return_date TEXT,
                date_returned TEXT,
                condition_out TEXT,
                condition_returned TEXT,
                charger_included INTEGER NOT NULL DEFAULT 0,
                charger_returned INTEGER,
                sim_moved INTEGER NOT NULL DEFAULT 0,
                outgoing_call_tested INTEGER NOT NULL DEFAULT 0,
                incoming_call_tested INTEGER NOT NULL DEFAULT 0,
                deposit_amount REAL NOT NULL DEFAULT 0,
                deposit_refunded REAL NOT NULL DEFAULT 0,
                deposit_deducted REAL NOT NULL DEFAULT 0,
                deduction_reason TEXT,
                agreement_signed INTEGER NOT NULL DEFAULT 0,
                checkout_staff TEXT,
                return_staff TEXT,
                status TEXT NOT NULL DEFAULT 'Checked Out',
                FOREIGN KEY (loaner_phone_id) REFERENCES loaner_phones(id),
                FOREIGN KEY (ticket_id) REFERENCES repair_tickets(id),
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS repair_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                default_policy TEXT,
                requires_soldering INTEGER NOT NULL DEFAULT 0,
                active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS pricing_defaults (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                base_labor_rate_per_hour REAL NOT NULL DEFAULT 60,
                minimum_labor_charge REAL NOT NULL DEFAULT 20,
                part_markup_percent REAL NOT NULL DEFAULT 0.35,
                diagnostic_fee REAL NOT NULL DEFAULT 20,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS pricing_brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS pricing_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (brand_id) REFERENCES pricing_brands(id),
                UNIQUE (brand_id, name)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS pricing_issue_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS pricing_repair_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS pricing_rules_catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER NOT NULL,
                model_id INTEGER NOT NULL,
                issue_type_id INTEGER NOT NULL,
                repair_type_id INTEGER NOT NULL,
                standard_price REAL NOT NULL,
                estimated_part_cost REAL NOT NULL DEFAULT 0,
                estimated_labor_minutes INTEGER NOT NULL DEFAULT 0,
                customer_wording TEXT,
                internal_notes TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (brand_id) REFERENCES pricing_brands(id),
                FOREIGN KEY (model_id) REFERENCES pricing_models(id),
                FOREIGN KEY (issue_type_id) REFERENCES pricing_issue_types(id),
                FOREIGN KEY (repair_type_id) REFERENCES pricing_repair_types(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS status_workflow_rules (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                transitions_json TEXT NOT NULL,
                guardrails_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS loaner_agreement_defaults (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                responsibility_text TEXT NOT NULL,
                return_policy_text TEXT NOT NULL,
                signature_note_text TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS notification_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_key TEXT UNIQUE NOT NULL,
                template_name TEXT NOT NULL,
                description TEXT NOT NULL,
                template_text TEXT NOT NULL,
                placeholders_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS technician_hours (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER,
                technician TEXT NOT NULL,
                work_date TEXT NOT NULL,
                hours_worked REAL NOT NULL,
                work_description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES repair_tickets(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS technician_clock_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER,
                technician TEXT NOT NULL,
                work_description TEXT,
                clocked_in_at TEXT NOT NULL,
                clocked_out_at TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES repair_tickets(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS parts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                part_number TEXT UNIQUE NOT NULL,
                part_name TEXT NOT NULL,
                device_compatibility TEXT,
                category TEXT NOT NULL,
                supplier TEXT,
                cost REAL,
                retail_price REAL,
                status TEXT NOT NULL DEFAULT 'In Stock',
                quantity_on_hand INTEGER NOT NULL DEFAULT 0,
                quantity_ordered INTEGER NOT NULL DEFAULT 0,
                reorder_level INTEGER NOT NULL DEFAULT 5,
                reorder_quantity INTEGER NOT NULL DEFAULT 10,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS donor_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_identifier TEXT UNIQUE NOT NULL,
                device_model TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Available for Parts',
                condition_notes TEXT,
                parts_harvested TEXT,
                parts_available TEXT,
                acquisition_date TEXT,
                retirement_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory_purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_date TEXT NOT NULL,
                vendor TEXT,
                reference_number TEXT,
                total_cost REAL NOT NULL DEFAULT 0,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory_purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,
                manufacturer TEXT,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                estimated_unit_cost REAL,
                line_total REAL,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (purchase_id) REFERENCES inventory_purchases(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS part_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repair_action_id INTEGER NOT NULL,
                part_id INTEGER NOT NULL,
                quantity_used INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (repair_action_id) REFERENCES repair_actions(id),
                FOREIGN KEY (part_id) REFERENCES parts(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                part_id INTEGER,
                donor_id INTEGER,
                movement_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                reason TEXT,
                ticket_id INTEGER,
                repair_action_id INTEGER,
                actor_user_id INTEGER,
                request_id TEXT,
                metadata_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (part_id) REFERENCES parts(id),
                FOREIGN KEY (donor_id) REFERENCES donor_devices(id),
                FOREIGN KEY (ticket_id) REFERENCES repair_tickets(id),
                FOREIGN KEY (repair_action_id) REFERENCES repair_actions(id)
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_inventory_movements_part_created
            ON inventory_movements(part_id, created_at)
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory_reconciliations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                part_id INTEGER NOT NULL,
                expected_quantity INTEGER NOT NULL,
                actual_quantity INTEGER NOT NULL,
                discrepancy INTEGER NOT NULL,
                reason TEXT NOT NULL,
                resolved_by TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (part_id) REFERENCES parts(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                entity_type TEXT NOT NULL,
                entity_id INTEGER,
                action TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                request_id TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attachment_type TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                storage_key TEXT NOT NULL UNIQUE,
                original_filename TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                uploaded_by INTEGER,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_attachments_entity
            ON attachments(entity_type, entity_id, created_at)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_activity_logs_entity
            ON activity_logs(entity_type, entity_id, created_at)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_activity_logs_action_created
            ON activity_logs(action, created_at)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_repair_tickets_status_updated
            ON repair_tickets(status, updated_at)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_repair_tickets_customer
            ON repair_tickets(customer_id)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_repair_tickets_assigned_status
            ON repair_tickets(assigned_technician, status)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_repair_tickets_created
            ON repair_tickets(created_at)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_ticket_history_ticket_created
            ON ticket_status_history(ticket_id, created_at)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_ticket_notes_ticket_created
            ON ticket_notes(ticket_id, created_at)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_loaner_checkouts_status_expected
            ON loaner_checkouts(status, expected_return_date)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_loaner_checkouts_ticket_status
            ON loaner_checkouts(ticket_id, status)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_parts_category_status_name
            ON parts(category, status, part_name)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_parts_stock_reorder
            ON parts(quantity_on_hand, reorder_level, status)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_donor_devices_status_model
            ON donor_devices(status, device_model)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_repair_actions_ticket_category
            ON repair_actions(ticket_id, repair_category_id)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_pricing_models_brand_active
            ON pricing_models(brand_id, active, name)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_pricing_rules_catalog_filters
            ON pricing_rules_catalog(brand_id, model_id, issue_type_id, repair_type_id, active)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_technician_hours_ticket_tech_date
            ON technician_hours(ticket_id, technician, work_date)
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS job_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idempotency_key TEXT NOT NULL UNIQUE,
                job_name TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS job_dead_letters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                queue TEXT NOT NULL,
                job_name TEXT NOT NULL,
                payload_json TEXT,
                attempts INTEGER NOT NULL,
                error_message TEXT NOT NULL,
                request_id TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS twilio_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                account_sid TEXT,
                auth_token_ciphertext TEXT,
                phone_number TEXT,
                public_webhook_base_url TEXT,
                voicemail_greeting TEXT,
                voicemail_greeting_audio_url TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        if not _table_has_column(connection, "twilio_settings", "voicemail_greeting_audio_url"):
            connection.execute(
                "ALTER TABLE twilio_settings ADD COLUMN voicemail_greeting_audio_url TEXT"
            )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS voicemail_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caller_number TEXT,
                called_number TEXT,
                call_sid TEXT,
                recording_sid TEXT,
                recording_url TEXT,
                recording_duration_seconds INTEGER,
                transcription_text TEXT,
                notes TEXT,
                status TEXT NOT NULL DEFAULT 'new',
                customer_id INTEGER,
                ticket_id INTEGER,
                listened_at TEXT,
                archived_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (ticket_id) REFERENCES repair_tickets(id)
            )
            """
        )
        seed_supported_device_models(connection)
        seed_repair_categories(connection)
        seed_pricing_defaults(connection)
        seed_pricing_catalog(connection)
        seed_status_workflow_rules(connection)
        seed_loaner_agreement_defaults(connection)
        seed_notification_templates(connection)
        seed_operational_records(connection)
        connection.commit()


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _get_twilio_cipher_secret() -> bytes:
    from app.core.settings import get_settings

    return hashlib.sha256(get_settings().signed_url_secret.encode("utf-8")).digest()


def _get_twilio_fernet() -> Fernet:
    key = base64.urlsafe_b64encode(_get_twilio_cipher_secret())
    return Fernet(key)


TWILIO_TOKEN_V2_PREFIX = "v2:"


def _encrypt_twilio_value_legacy(value: str) -> str:
    secret = _get_twilio_cipher_secret()
    raw = value.encode("utf-8")
    encrypted = bytes(byte ^ secret[index % len(secret)] for index, byte in enumerate(raw))
    return base64.urlsafe_b64encode(encrypted).decode("ascii")


def _decrypt_twilio_value_legacy(value: str | None) -> str | None:
    if not value:
        return None

    secret = _get_twilio_cipher_secret()
    try:
        raw = base64.urlsafe_b64decode(value.encode("ascii"))
    except (ValueError, UnicodeError):
        return None

    decrypted = bytes(byte ^ secret[index % len(secret)] for index, byte in enumerate(raw))
    try:
        return decrypted.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _encrypt_twilio_value(value: str) -> str:
    token = _get_twilio_fernet().encrypt(value.encode("utf-8")).decode("ascii")
    return f"{TWILIO_TOKEN_V2_PREFIX}{token}"


def _decrypt_twilio_value(value: str | None) -> str | None:
    if not value:
        return None

    if value.startswith(TWILIO_TOKEN_V2_PREFIX):
        encrypted = value.removeprefix(TWILIO_TOKEN_V2_PREFIX)
        try:
            return _get_twilio_fernet().decrypt(encrypted.encode("ascii")).decode("utf-8")
        except (InvalidToken, ValueError, UnicodeError):
            return None

    # Backward compatibility for pre-v2 records.
    return _decrypt_twilio_value_legacy(value)


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row is not None else None


def to_bool(value: int | None) -> bool | None:
    if value is None:
        return None
    return bool(value)


def build_device_label(row: sqlite3.Row | dict) -> str:
    device_model_text_override = row["device_model_text_override"]
    if device_model_text_override:
        return device_model_text_override

    manufacturer = row["manufacturer"] if "manufacturer" in row.keys() else None
    model_name = row["model_name"] if "model_name" in row.keys() else None
    if manufacturer and model_name:
        return f"{manufacturer} {model_name}"
    if model_name:
        return model_name
    return "Unknown Device"


DIFFICULTY_MULTIPLIERS = {
    1: 1.00,
    2: 1.15,
    3: 1.30,
    4: 1.50,
    5: 1.75,
}


RISK_MULTIPLIERS = {
    1: 1.00,
    2: 1.10,
    3: 1.20,
    4: 1.35,
    5: 1.50,
}

DEFAULT_PRICING_DEFAULTS = {
    "base_labor_rate_per_hour": 60.0,
    "minimum_labor_charge": 20.0,
    "part_markup_percent": 0.35,
    "diagnostic_fee": 20.0,
}

DEFAULT_PRICING_BRANDS = [
    "CAT",
    "FIG",
    "Kyocera",
    "LG",
    "Qin",
    "Wonder",
]

DEFAULT_PRICING_MODELS = {
    "CAT": ["S22"],
    "FIG": ["FIG", "FIG Mini"],
    "Kyocera": ["E4610", "E4810", "E4811", "E4830", "E4831", "S2720/Cadence"],
    "LG": ["Classic", "Exalt"],
    "Qin": ["Qin"],
    "Wonder": ["Wonder"],
}

DEFAULT_PRICING_ISSUE_TYPES = [
    "Battery",
    "Charging Cleaning",
    "Charging Port",
    "Hinge/Housing",
    "Keypad/Buttons",
    "Screen/LCD",
]

DEFAULT_PRICING_REPAIR_TYPES = [
    "Estimate",
    "Repair",
]

DEFAULT_PRICING_RULES = [
    {
        "brand": "Kyocera",
        "model": "E4610",
        "issue_type": "Battery",
        "repair_type": "Estimate",
        "standard_price": 45,
        "estimated_part_cost": 18,
        "estimated_labor_minutes": 20,
        "customer_wording": "Battery replacement usually lands in the $35-$50 range.",
        "internal_notes": "Repair-first if parts are available.",
    },
    {
        "brand": "Kyocera",
        "model": "E4610",
        "issue_type": "Screen/LCD",
        "repair_type": "Estimate",
        "standard_price": 90,
        "estimated_part_cost": 35,
        "estimated_labor_minutes": 45,
        "customer_wording": "Screen/LCD usually lands in the $65-$120 range.",
        "internal_notes": "Repair-first if parts are available.",
    },
    {
        "brand": "Kyocera",
        "model": "E4610",
        "issue_type": "Hinge/Housing",
        "repair_type": "Estimate",
        "standard_price": 95,
        "estimated_part_cost": 36,
        "estimated_labor_minutes": 50,
        "customer_wording": "Hinge/housing work usually lands in the $65-$125 range.",
        "internal_notes": "Repair-first if parts are available.",
    },
    {
        "brand": "Kyocera",
        "model": "S2720/Cadence",
        "issue_type": "Battery",
        "repair_type": "Estimate",
        "standard_price": 40,
        "estimated_part_cost": 15,
        "estimated_labor_minutes": 20,
        "customer_wording": "Battery replacement usually lands in the $30-$45 range.",
        "internal_notes": "Soldering charging-port repairs are not offered.",
    },
    {
        "brand": "Kyocera",
        "model": "E4810",
        "issue_type": "Battery",
        "repair_type": "Estimate",
        "standard_price": 45,
        "estimated_part_cost": 18,
        "estimated_labor_minutes": 20,
        "customer_wording": "Battery replacement usually lands in the $35-$55 range.",
        "internal_notes": "Main supported rugged flip model line.",
    },
    {
        "brand": "LG",
        "model": "Classic",
        "issue_type": "Screen/LCD",
        "repair_type": "Estimate",
        "standard_price": 65,
        "estimated_part_cost": 25,
        "estimated_labor_minutes": 35,
        "customer_wording": "Screen/LCD usually lands in the $45-$85 range.",
        "internal_notes": "Repair if cost-effective for customer.",
    },
    {
        "brand": "LG",
        "model": "Exalt",
        "issue_type": "Screen/LCD",
        "repair_type": "Estimate",
        "standard_price": 75,
        "estimated_part_cost": 28,
        "estimated_labor_minutes": 35,
        "customer_wording": "Screen/LCD usually lands in the $55-$95 range.",
        "internal_notes": "Repair if customer strongly values device.",
    },
    {
        "brand": "CAT",
        "model": "S22",
        "issue_type": "Battery",
        "repair_type": "Estimate",
        "standard_price": 60,
        "estimated_part_cost": 26,
        "estimated_labor_minutes": 30,
        "customer_wording": "Battery replacement usually lands in the $45-$75 range.",
        "internal_notes": "Smart-flip model; labor can run long.",
    },
    {
        "brand": "FIG",
        "model": "FIG Mini",
        "issue_type": "Hinge/Housing",
        "repair_type": "Estimate",
        "standard_price": 145,
        "estimated_part_cost": 55,
        "estimated_labor_minutes": 60,
        "customer_wording": "Hinge/housing usually lands in the $125-$165 range.",
        "internal_notes": "Battery/shell/setup focus.",
    },
    {
        "brand": "Kyocera",
        "model": "E4810",
        "issue_type": "Charging Cleaning",
        "repair_type": "Repair",
        "standard_price": 15,
        "estimated_part_cost": 0,
        "estimated_labor_minutes": 10,
        "customer_wording": "Charging port cleaning is a flat $15.",
        "internal_notes": "Quick clean is recommended before any port quote.",
    },
]

def build_default_status_workflow_transitions() -> dict[str, list[str]]:
    return {
        "New Intake": ["Needs Diagnosis"],
        "Needs Diagnosis": ["Diagnosed", "Not Repairable", "Returned Unrepaired"],
        "Diagnosed": ["Approved", "Customer Approval Needed", "Waiting for Parts", "Replaced Instead"],
        "Customer Approval Needed": ["Approved", "Customer Declined"],
        "Customer Declined": ["Returned Unrepaired"],
        "Approved": ["Ready for Repair"],
        "Waiting for Parts": ["Ready for Repair"],
        "Ready for Repair": ["In Repair"],
        "In Repair": ["Ready for Pickup"],
        "Ready for Pickup": ["Picked Up / Closed"],
        "Replaced Instead": ["Picked Up / Closed"],
        "Picked Up / Closed": [],
        "Not Repairable": [],
        "Returned Unrepaired": [],
    }

DEFAULT_STATUS_WORKFLOW_GUARDRAILS = {
    "enforce_no_active_loaner_for_ready_for_pickup": True,
    "enforce_no_active_loaner_for_closed_statuses": True,
    "enforce_final_price_for_ready_for_pickup": True,
    "enforce_final_price_for_closed_paid_statuses": True,
}

DEFAULT_LOANER_AGREEMENT_DEFAULTS = {
    "responsibility_text": (
        "Customer accepts responsibility for the loaner device and listed accessories. "
        "Loss or damage may result in deductible charges."
    ),
    "return_policy_text": (
        "Loaner device should be returned in similar condition when repair pickup is completed."
    ),
    "signature_note_text": "By signing, both parties acknowledge the checkout details above.",
}

DEFAULT_NOTIFICATION_TEMPLATES = {
    "diagnosis_complete": {
        "template_name": "Diagnosis complete – approval needed",
        "description": "Sent when diagnosis is complete and customer approval is needed for repair",
        "template_text": (
            "Hello, this is Tech Restore Phone Repair. We diagnosed your [MODEL]. "
            "The estimated repair price is $[AMOUNT]. Please reply/confirm if you approve the repair."
        ),
        "placeholders": ["MODEL", "AMOUNT"],
    },
    "ready_for_pickup": {
        "template_name": "Ready for pickup",
        "description": "Sent when the repaired device is ready for customer pickup",
        "template_text": (
            "Hello, this is Tech Restore Phone Repair. Your [MODEL] is ready for pickup. "
            "Final amount due: $[AMOUNT]. Please bring back loaner [LOANER_ID] if one was issued."
        ),
        "placeholders": ["MODEL", "AMOUNT", "LOANER_ID"],
    },
    "waiting_for_parts": {
        "template_name": "Waiting for parts",
        "description": "Sent when repair is paused waiting for a part to arrive",
        "template_text": (
            "Hello, this is Tech Restore Phone Repair. Your [MODEL] repair is waiting for a part. "
            "We will update you when it is ready."
        ),
        "placeholders": ["MODEL"],
    },
    "not_worth_repair": {
        "template_name": "Not worth repair",
        "description": "Sent when diagnosis suggests repair cost is higher than replacement",
        "template_text": (
            "Hello, this is Tech Restore Phone Repair. After diagnosis, the repair cost for your [MODEL] "
            "may not be worth it compared to replacement. Please contact us to discuss options."
        ),
        "placeholders": ["MODEL"],
    },
    "loaner_overdue": {
        "template_name": "Loaner overdue",
        "description": "Sent as reminder when a checked-out loaner device is overdue for return",
        "template_text": (
            "Hello, this is Tech Restore Phone Repair. Our records show loaner [LOANER_ID] is still checked out. "
            "Please return it as soon as possible or contact us."
        ),
        "placeholders": ["LOANER_ID"],
    },
}


def round_customer_price(amount: float) -> float:
    if amount < 50:
        return round(amount / 5) * 5
    return round(amount / 10) * 10


def seed_supported_device_models(connection: sqlite3.Connection) -> None:
    existing_count = connection.execute(
        "SELECT COUNT(*) AS count FROM supported_device_models"
    ).fetchone()["count"]
    if existing_count:
        return

    connection.executemany(
        """
        INSERT INTO supported_device_models (
            manufacturer,
            device_family,
            model_name,
            model_aliases,
            repair_policy,
            notes,
            active
        ) VALUES (?, ?, ?, ?, ?, ?, 1)
        """,
        [
            (
                model["manufacturer"],
                model["device_family"],
                model["model_name"],
                model["model_aliases"],
                model["repair_policy"],
                model["notes"],
            )
            for model in SUPPORTED_DEVICE_MODELS
        ],
    )


def seed_repair_categories(connection: sqlite3.Connection) -> None:
    existing_count = connection.execute(
        "SELECT COUNT(*) AS count FROM repair_categories"
    ).fetchone()["count"]
    if existing_count:
        return

    connection.executemany(
        """
        INSERT INTO repair_categories (
            name,
            description,
            default_policy,
            requires_soldering,
            active
        ) VALUES (?, ?, ?, ?, 1)
        """,
        [
            (
                category["name"],
                category["description"],
                category["default_policy"],
                category["requires_soldering"],
            )
            for category in REPAIR_CATEGORIES
        ],
    )


def get_seed_counts() -> dict[str, int]:
    with get_connection() as connection:
        models_count = connection.execute(
            "SELECT COUNT(*) AS count FROM supported_device_models"
        ).fetchone()["count"]
        repair_categories_count = connection.execute(
            "SELECT COUNT(*) AS count FROM repair_categories"
        ).fetchone()["count"]
    return {
        "supported_model_count": models_count,
        "repair_category_count": repair_categories_count,
    }


def list_supported_models() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, manufacturer, device_family, model_name, model_aliases, repair_policy, notes
            FROM supported_device_models
            WHERE active = 1
            ORDER BY manufacturer, model_name
            """
        ).fetchall()
    return [dict(row) for row in rows]


def list_repair_categories() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, description, default_policy, requires_soldering
            FROM repair_categories
            WHERE active = 1
            ORDER BY name ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def list_repair_categories_for_management(include_inactive: bool = False) -> list[dict]:
    where_clause = "" if include_inactive else "WHERE active = 1"
    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT id, name, description, default_policy, requires_soldering, active
            FROM repair_categories
            {where_clause}
            ORDER BY active DESC, name ASC
            """
        ).fetchall()
    return [
        {
            **dict(row),
            "requires_soldering": bool(row["requires_soldering"]),
            "active": bool(row["active"]),
        }
        for row in rows
    ]


def create_repair_category(payload: dict) -> dict:
    with get_connection() as connection:
        try:
            cursor = connection.execute(
                """
                INSERT INTO repair_categories (name, description, default_policy, requires_soldering, active)
                VALUES (?, ?, ?, ?, 1)
                """,
                (
                    payload["name"].strip(),
                    payload.get("description"),
                    payload.get("default_policy"),
                    1 if payload.get("requires_soldering", False) else 0,
                ),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("A repair category with that name already exists") from error
        connection.commit()
        created = connection.execute(
            """
            SELECT id, name, description, default_policy, requires_soldering, active
            FROM repair_categories
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    if not created:
        raise ValueError("Repair category could not be created")
    return {
        **dict(created),
        "requires_soldering": bool(created["requires_soldering"]),
        "active": bool(created["active"]),
    }


def update_repair_category(repair_category_id: int, payload: dict) -> dict | None:
    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT id, name, description, default_policy, requires_soldering, active
            FROM repair_categories
            WHERE id = ?
            """,
            (repair_category_id,),
        ).fetchone()
        if existing is None:
            return None

        next_name = payload.get("name", existing["name"])
        if isinstance(next_name, str):
            next_name = next_name.strip()
        updates = {
            "name": next_name,
            "description": payload.get("description", existing["description"]),
            "default_policy": payload.get("default_policy", existing["default_policy"]),
            "requires_soldering": (
                1 if payload.get("requires_soldering", bool(existing["requires_soldering"])) else 0
            ),
            "active": 1 if payload.get("active", bool(existing["active"])) else 0,
        }
        try:
            connection.execute(
                """
                UPDATE repair_categories
                SET name = ?,
                    description = ?,
                    default_policy = ?,
                    requires_soldering = ?,
                    active = ?
                WHERE id = ?
                """,
                (
                    updates["name"],
                    updates["description"],
                    updates["default_policy"],
                    updates["requires_soldering"],
                    updates["active"],
                    repair_category_id,
                ),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("A repair category with that name already exists") from error
        connection.commit()
        updated = connection.execute(
            """
            SELECT id, name, description, default_policy, requires_soldering, active
            FROM repair_categories
            WHERE id = ?
            """,
            (repair_category_id,),
        ).fetchone()

    if not updated:
        return None
    return {
        **dict(updated),
        "requires_soldering": bool(updated["requires_soldering"]),
        "active": bool(updated["active"]),
    }


def seed_pricing_defaults(connection: sqlite3.Connection) -> None:
    existing = connection.execute("SELECT id FROM pricing_defaults WHERE id = 1").fetchone()
    if existing:
        return

    connection.execute(
        """
        INSERT INTO pricing_defaults (
            id,
            base_labor_rate_per_hour,
            minimum_labor_charge,
            part_markup_percent,
            diagnostic_fee,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            DEFAULT_PRICING_DEFAULTS["base_labor_rate_per_hour"],
            DEFAULT_PRICING_DEFAULTS["minimum_labor_charge"],
            DEFAULT_PRICING_DEFAULTS["part_markup_percent"],
            DEFAULT_PRICING_DEFAULTS["diagnostic_fee"],
            utc_now(),
        ),
    )


def get_pricing_defaults() -> dict:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT base_labor_rate_per_hour, minimum_labor_charge, part_markup_percent, diagnostic_fee
            FROM pricing_defaults
            WHERE id = 1
            """
        ).fetchone()

    if not row:
        return DEFAULT_PRICING_DEFAULTS.copy()

    return {
        "base_labor_rate_per_hour": float(row["base_labor_rate_per_hour"]),
        "minimum_labor_charge": float(row["minimum_labor_charge"]),
        "part_markup_percent": float(row["part_markup_percent"]),
        "diagnostic_fee": float(row["diagnostic_fee"]),
    }


def update_pricing_defaults(payload: dict) -> dict:
    existing = get_pricing_defaults()
    updated = {
        "base_labor_rate_per_hour": float(payload.get("base_labor_rate_per_hour", existing["base_labor_rate_per_hour"])),
        "minimum_labor_charge": float(payload.get("minimum_labor_charge", existing["minimum_labor_charge"])),
        "part_markup_percent": float(payload.get("part_markup_percent", existing["part_markup_percent"])),
        "diagnostic_fee": float(payload.get("diagnostic_fee", existing["diagnostic_fee"])),
    }

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO pricing_defaults (
                id,
                base_labor_rate_per_hour,
                minimum_labor_charge,
                part_markup_percent,
                diagnostic_fee,
                updated_at
            ) VALUES (1, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                base_labor_rate_per_hour = excluded.base_labor_rate_per_hour,
                minimum_labor_charge = excluded.minimum_labor_charge,
                part_markup_percent = excluded.part_markup_percent,
                diagnostic_fee = excluded.diagnostic_fee,
                updated_at = excluded.updated_at
            """,
            (
                updated["base_labor_rate_per_hour"],
                updated["minimum_labor_charge"],
                updated["part_markup_percent"],
                updated["diagnostic_fee"],
                utc_now(),
            ),
        )
        connection.commit()

    return get_pricing_defaults()


def seed_pricing_catalog(connection: sqlite3.Connection) -> None:
    existing_count = connection.execute(
        "SELECT COUNT(*) AS count FROM pricing_rules_catalog"
    ).fetchone()["count"]
    if existing_count:
        return

    timestamp = utc_now()
    for brand_name in DEFAULT_PRICING_BRANDS:
        connection.execute(
            """
            INSERT INTO pricing_brands (name, active, created_at, updated_at)
            VALUES (?, 1, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                active = excluded.active,
                updated_at = excluded.updated_at
            """,
            (brand_name, timestamp, timestamp),
        )

    brand_rows = connection.execute(
        "SELECT id, name FROM pricing_brands"
    ).fetchall()
    brand_id_by_name = {row["name"]: int(row["id"]) for row in brand_rows}

    for brand_name, models in DEFAULT_PRICING_MODELS.items():
        brand_id = brand_id_by_name.get(brand_name)
        if brand_id is None:
            continue
        for model_name in models:
            connection.execute(
                """
                INSERT INTO pricing_models (brand_id, name, active, created_at, updated_at)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(brand_id, name) DO UPDATE SET
                    active = excluded.active,
                    updated_at = excluded.updated_at
                """,
                (brand_id, model_name, timestamp, timestamp),
            )

    for issue_type in DEFAULT_PRICING_ISSUE_TYPES:
        connection.execute(
            """
            INSERT INTO pricing_issue_types (name, active, created_at, updated_at)
            VALUES (?, 1, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                active = excluded.active,
                updated_at = excluded.updated_at
            """,
            (issue_type, timestamp, timestamp),
        )

    for repair_type in DEFAULT_PRICING_REPAIR_TYPES:
        connection.execute(
            """
            INSERT INTO pricing_repair_types (name, active, created_at, updated_at)
            VALUES (?, 1, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                active = excluded.active,
                updated_at = excluded.updated_at
            """,
            (repair_type, timestamp, timestamp),
        )

    model_rows = connection.execute(
        """
        SELECT m.id, m.name, b.name AS brand_name
        FROM pricing_models m
        JOIN pricing_brands b ON b.id = m.brand_id
        """
    ).fetchall()
    model_id_by_key = {(row["brand_name"], row["name"]): int(row["id"]) for row in model_rows}

    issue_rows = connection.execute(
        "SELECT id, name FROM pricing_issue_types"
    ).fetchall()
    issue_id_by_name = {row["name"]: int(row["id"]) for row in issue_rows}

    repair_rows = connection.execute(
        "SELECT id, name FROM pricing_repair_types"
    ).fetchall()
    repair_id_by_name = {row["name"]: int(row["id"]) for row in repair_rows}

    for rule in DEFAULT_PRICING_RULES:
        brand_id = brand_id_by_name.get(rule["brand"])
        model_id = model_id_by_key.get((rule["brand"], rule["model"]))
        issue_type_id = issue_id_by_name.get(rule["issue_type"])
        repair_type_id = repair_id_by_name.get(rule["repair_type"])
        if not brand_id or not model_id or not issue_type_id or not repair_type_id:
            continue

        connection.execute(
            """
            INSERT INTO pricing_rules_catalog (
                brand_id,
                model_id,
                issue_type_id,
                repair_type_id,
                standard_price,
                estimated_part_cost,
                estimated_labor_minutes,
                customer_wording,
                internal_notes,
                active,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                brand_id,
                model_id,
                issue_type_id,
                repair_type_id,
                float(rule["standard_price"]),
                float(rule["estimated_part_cost"]),
                int(rule["estimated_labor_minutes"]),
                rule.get("customer_wording"),
                rule.get("internal_notes"),
                timestamp,
                timestamp,
            ),
        )


def _bool_to_int(value: bool) -> int:
    return 1 if value else 0


def list_pricing_brands(include_inactive: bool = True) -> list[dict]:
    where_clause = "" if include_inactive else "WHERE active = 1"
    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT id, name, active, created_at, updated_at
            FROM pricing_brands
            {where_clause}
            ORDER BY active DESC, name ASC
            """
        ).fetchall()
    return [{**dict(row), "active": bool(row["active"])} for row in rows]


def create_pricing_brand(payload: dict) -> dict:
    name = str(payload.get("name") or "").strip()
    if not name:
        raise ValueError("Brand name is required")
    now = utc_now()
    with get_connection() as connection:
        try:
            cursor = connection.execute(
                """
                INSERT INTO pricing_brands (name, active, created_at, updated_at)
                VALUES (?, 1, ?, ?)
                """,
                (name, now, now),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("A brand with that name already exists") from error
        connection.commit()
        row = connection.execute(
            "SELECT id, name, active, created_at, updated_at FROM pricing_brands WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    if row is None:
        raise ValueError("Brand could not be created")
    return {**dict(row), "active": bool(row["active"])}


def update_pricing_brand(brand_id: int, payload: dict) -> dict | None:
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id, name, active, created_at, updated_at FROM pricing_brands WHERE id = ?",
            (brand_id,),
        ).fetchone()
        if existing is None:
            return None
        name = payload.get("name", existing["name"])
        if isinstance(name, str):
            name = name.strip()
        if not name:
            raise ValueError("Brand name is required")
        active = bool(payload.get("active", bool(existing["active"])))
        try:
            connection.execute(
                """
                UPDATE pricing_brands
                SET name = ?,
                    active = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (name, _bool_to_int(active), utc_now(), brand_id),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("A brand with that name already exists") from error
        connection.commit()
        row = connection.execute(
            "SELECT id, name, active, created_at, updated_at FROM pricing_brands WHERE id = ?",
            (brand_id,),
        ).fetchone()
    return None if row is None else {**dict(row), "active": bool(row["active"])}


def list_pricing_models(brand_id: int | None = None, include_inactive: bool = True) -> list[dict]:
    predicates: list[str] = []
    params: list[int] = []
    if brand_id is not None:
        predicates.append("m.brand_id = ?")
        params.append(brand_id)
    if not include_inactive:
        predicates.append("m.active = 1")
    where_clause = f"WHERE {' AND '.join(predicates)}" if predicates else ""

    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT
                m.id,
                m.brand_id,
                b.name AS brand_name,
                m.name,
                m.active,
                m.created_at,
                m.updated_at
            FROM pricing_models m
            JOIN pricing_brands b ON b.id = m.brand_id
            {where_clause}
            ORDER BY m.active DESC, b.name ASC, m.name ASC
            """,
            tuple(params),
        ).fetchall()
    return [{**dict(row), "active": bool(row["active"])} for row in rows]


def create_pricing_model(payload: dict) -> dict:
    brand_id = int(payload.get("brand_id") or 0)
    name = str(payload.get("name") or "").strip()
    if brand_id <= 0:
        raise ValueError("brand_id is required")
    if not name:
        raise ValueError("Model name is required")

    now = utc_now()
    with get_connection() as connection:
        brand_exists = connection.execute(
            "SELECT id FROM pricing_brands WHERE id = ?",
            (brand_id,),
        ).fetchone()
        if brand_exists is None:
            raise ValueError("Selected brand does not exist")
        try:
            cursor = connection.execute(
                """
                INSERT INTO pricing_models (brand_id, name, active, created_at, updated_at)
                VALUES (?, ?, 1, ?, ?)
                """,
                (brand_id, name, now, now),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("A model with that name already exists for this brand") from error
        connection.commit()
        row = connection.execute(
            """
            SELECT m.id, m.brand_id, b.name AS brand_name, m.name, m.active, m.created_at, m.updated_at
            FROM pricing_models m
            JOIN pricing_brands b ON b.id = m.brand_id
            WHERE m.id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    if row is None:
        raise ValueError("Model could not be created")
    return {**dict(row), "active": bool(row["active"])}


def update_pricing_model(model_id: int, payload: dict) -> dict | None:
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id, brand_id, name, active FROM pricing_models WHERE id = ?",
            (model_id,),
        ).fetchone()
        if existing is None:
            return None

        brand_id = int(payload.get("brand_id", existing["brand_id"]))
        name = payload.get("name", existing["name"])
        if isinstance(name, str):
            name = name.strip()
        if not name:
            raise ValueError("Model name is required")
        active = bool(payload.get("active", bool(existing["active"])))

        brand_exists = connection.execute(
            "SELECT id FROM pricing_brands WHERE id = ?",
            (brand_id,),
        ).fetchone()
        if brand_exists is None:
            raise ValueError("Selected brand does not exist")

        try:
            connection.execute(
                """
                UPDATE pricing_models
                SET brand_id = ?,
                    name = ?,
                    active = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (brand_id, name, _bool_to_int(active), utc_now(), model_id),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("A model with that name already exists for this brand") from error
        connection.commit()
        row = connection.execute(
            """
            SELECT m.id, m.brand_id, b.name AS brand_name, m.name, m.active, m.created_at, m.updated_at
            FROM pricing_models m
            JOIN pricing_brands b ON b.id = m.brand_id
            WHERE m.id = ?
            """,
            (model_id,),
        ).fetchone()
    return None if row is None else {**dict(row), "active": bool(row["active"])}


def _list_simple_pricing_dimension(table_name: str, include_inactive: bool = True) -> list[dict]:
    where_clause = "" if include_inactive else "WHERE active = 1"
    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT id, name, active, created_at, updated_at
            FROM {table_name}
            {where_clause}
            ORDER BY active DESC, name ASC
            """
        ).fetchall()
    return [{**dict(row), "active": bool(row["active"])} for row in rows]


def list_pricing_issue_types(include_inactive: bool = True) -> list[dict]:
    return _list_simple_pricing_dimension("pricing_issue_types", include_inactive=include_inactive)


def list_pricing_repair_types(include_inactive: bool = True) -> list[dict]:
    return _list_simple_pricing_dimension("pricing_repair_types", include_inactive=include_inactive)


def _create_simple_pricing_dimension(table_name: str, payload: dict, singular: str) -> dict:
    name = str(payload.get("name") or "").strip()
    if not name:
        raise ValueError(f"{singular} name is required")
    now = utc_now()
    with get_connection() as connection:
        try:
            cursor = connection.execute(
                f"""
                INSERT INTO {table_name} (name, active, created_at, updated_at)
                VALUES (?, 1, ?, ?)
                """,
                (name, now, now),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError(f"A {singular.lower()} with that name already exists") from error
        connection.commit()
        row = connection.execute(
            f"SELECT id, name, active, created_at, updated_at FROM {table_name} WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    if row is None:
        raise ValueError(f"{singular} could not be created")
    return {**dict(row), "active": bool(row["active"])}


def _update_simple_pricing_dimension(table_name: str, entity_id: int, payload: dict, singular: str) -> dict | None:
    with get_connection() as connection:
        existing = connection.execute(
            f"SELECT id, name, active FROM {table_name} WHERE id = ?",
            (entity_id,),
        ).fetchone()
        if existing is None:
            return None
        name = payload.get("name", existing["name"])
        if isinstance(name, str):
            name = name.strip()
        if not name:
            raise ValueError(f"{singular} name is required")
        active = bool(payload.get("active", bool(existing["active"])))
        try:
            connection.execute(
                f"""
                UPDATE {table_name}
                SET name = ?,
                    active = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (name, _bool_to_int(active), utc_now(), entity_id),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError(f"A {singular.lower()} with that name already exists") from error
        connection.commit()
        row = connection.execute(
            f"SELECT id, name, active, created_at, updated_at FROM {table_name} WHERE id = ?",
            (entity_id,),
        ).fetchone()
    return None if row is None else {**dict(row), "active": bool(row["active"])}


def create_pricing_issue_type(payload: dict) -> dict:
    return _create_simple_pricing_dimension("pricing_issue_types", payload, "Issue type")


def update_pricing_issue_type(issue_type_id: int, payload: dict) -> dict | None:
    return _update_simple_pricing_dimension("pricing_issue_types", issue_type_id, payload, "Issue type")


def create_pricing_repair_type(payload: dict) -> dict:
    return _create_simple_pricing_dimension("pricing_repair_types", payload, "Repair type")


def update_pricing_repair_type(repair_type_id: int, payload: dict) -> dict | None:
    return _update_simple_pricing_dimension("pricing_repair_types", repair_type_id, payload, "Repair type")


def _pricing_rules_base_query() -> str:
    return """
        SELECT
            r.id,
            r.brand_id,
            b.name AS brand_name,
            r.model_id,
            m.name AS model_name,
            r.issue_type_id,
            i.name AS issue_type_name,
            r.repair_type_id,
            t.name AS repair_type_name,
            r.standard_price,
            r.estimated_part_cost,
            r.estimated_labor_minutes,
            r.active,
            r.customer_wording,
            r.internal_notes,
            r.created_at,
            r.updated_at
        FROM pricing_rules_catalog r
        JOIN pricing_brands b ON b.id = r.brand_id
        JOIN pricing_models m ON m.id = r.model_id
        JOIN pricing_issue_types i ON i.id = r.issue_type_id
        JOIN pricing_repair_types t ON t.id = r.repair_type_id
    """


def list_pricing_rules(filters: dict | None = None) -> list[dict]:
    filters = filters or {}
    predicates: list[str] = []
    params: list[object] = []

    if filters.get("brand_id") is not None:
        predicates.append("r.brand_id = ?")
        params.append(int(filters["brand_id"]))
    if filters.get("model_id") is not None:
        predicates.append("r.model_id = ?")
        params.append(int(filters["model_id"]))
    if filters.get("issue_type_id") is not None:
        predicates.append("r.issue_type_id = ?")
        params.append(int(filters["issue_type_id"]))
    if filters.get("repair_type_id") is not None:
        predicates.append("r.repair_type_id = ?")
        params.append(int(filters["repair_type_id"]))
    if not bool(filters.get("include_inactive", False)):
        predicates.append("r.active = 1")

    search = str(filters.get("search") or "").strip()
    if search:
        predicates.append("(b.name LIKE ? OR m.name LIKE ? OR i.name LIKE ? OR t.name LIKE ? OR IFNULL(r.customer_wording, '') LIKE ? OR IFNULL(r.internal_notes, '') LIKE ?)")
        pattern = f"%{search}%"
        params.extend([pattern, pattern, pattern, pattern, pattern, pattern])

    where_clause = f"WHERE {' AND '.join(predicates)}" if predicates else ""
    with get_connection() as connection:
        rows = connection.execute(
            f"""
            {_pricing_rules_base_query()}
            {where_clause}
            ORDER BY r.active DESC, b.name ASC, m.name ASC, i.name ASC, t.name ASC
            """,
            tuple(params),
        ).fetchall()
    return [
        {
            **dict(row),
            "active": bool(row["active"]),
            "standard_price": float(row["standard_price"]),
            "estimated_part_cost": float(row["estimated_part_cost"]),
            "estimated_labor_minutes": int(row["estimated_labor_minutes"]),
        }
        for row in rows
    ]


def create_pricing_rule(payload: dict) -> dict:
    required_ids = {
        "brand_id": int(payload.get("brand_id") or 0),
        "model_id": int(payload.get("model_id") or 0),
        "issue_type_id": int(payload.get("issue_type_id") or 0),
        "repair_type_id": int(payload.get("repair_type_id") or 0),
    }
    if any(value <= 0 for value in required_ids.values()):
        raise ValueError("brand_id, model_id, issue_type_id, and repair_type_id are required")

    now = utc_now()
    with get_connection() as connection:
        try:
            cursor = connection.execute(
                """
                INSERT INTO pricing_rules_catalog (
                    brand_id,
                    model_id,
                    issue_type_id,
                    repair_type_id,
                    standard_price,
                    estimated_part_cost,
                    estimated_labor_minutes,
                    customer_wording,
                    internal_notes,
                    active,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    required_ids["brand_id"],
                    required_ids["model_id"],
                    required_ids["issue_type_id"],
                    required_ids["repair_type_id"],
                    float(payload.get("standard_price", 0)),
                    float(payload.get("estimated_part_cost", 0)),
                    int(payload.get("estimated_labor_minutes", 0)),
                    payload.get("customer_wording"),
                    payload.get("internal_notes"),
                    _bool_to_int(bool(payload.get("active", True))),
                    now,
                    now,
                ),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("Pricing rule references an invalid brand, model, issue type, or repair type") from error
        connection.commit()
        row = connection.execute(
            f"""
            {_pricing_rules_base_query()}
            WHERE r.id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

    if row is None:
        raise ValueError("Pricing rule could not be created")
    result = dict(row)
    result["active"] = bool(row["active"])
    result["standard_price"] = float(row["standard_price"])
    result["estimated_part_cost"] = float(row["estimated_part_cost"])
    result["estimated_labor_minutes"] = int(row["estimated_labor_minutes"])
    return result


def update_pricing_rule(rule_id: int, payload: dict) -> dict | None:
    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT
                id,
                brand_id,
                model_id,
                issue_type_id,
                repair_type_id,
                standard_price,
                estimated_part_cost,
                estimated_labor_minutes,
                customer_wording,
                internal_notes,
                active
            FROM pricing_rules_catalog
            WHERE id = ?
            """,
            (rule_id,),
        ).fetchone()
        if existing is None:
            return None

        updates = {
            "brand_id": int(payload.get("brand_id", existing["brand_id"])),
            "model_id": int(payload.get("model_id", existing["model_id"])),
            "issue_type_id": int(payload.get("issue_type_id", existing["issue_type_id"])),
            "repair_type_id": int(payload.get("repair_type_id", existing["repair_type_id"])),
            "standard_price": float(payload.get("standard_price", existing["standard_price"])),
            "estimated_part_cost": float(payload.get("estimated_part_cost", existing["estimated_part_cost"])),
            "estimated_labor_minutes": int(payload.get("estimated_labor_minutes", existing["estimated_labor_minutes"])),
            "customer_wording": payload.get("customer_wording", existing["customer_wording"]),
            "internal_notes": payload.get("internal_notes", existing["internal_notes"]),
            "active": _bool_to_int(bool(payload.get("active", bool(existing["active"])))),
        }

        try:
            connection.execute(
                """
                UPDATE pricing_rules_catalog
                SET brand_id = ?,
                    model_id = ?,
                    issue_type_id = ?,
                    repair_type_id = ?,
                    standard_price = ?,
                    estimated_part_cost = ?,
                    estimated_labor_minutes = ?,
                    customer_wording = ?,
                    internal_notes = ?,
                    active = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    updates["brand_id"],
                    updates["model_id"],
                    updates["issue_type_id"],
                    updates["repair_type_id"],
                    updates["standard_price"],
                    updates["estimated_part_cost"],
                    updates["estimated_labor_minutes"],
                    updates["customer_wording"],
                    updates["internal_notes"],
                    updates["active"],
                    utc_now(),
                    rule_id,
                ),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("Pricing rule references an invalid brand, model, issue type, or repair type") from error
        connection.commit()
        row = connection.execute(
            f"""
            {_pricing_rules_base_query()}
            WHERE r.id = ?
            """,
            (rule_id,),
        ).fetchone()
    if row is None:
        return None
    result = dict(row)
    result["active"] = bool(row["active"])
    result["standard_price"] = float(row["standard_price"])
    result["estimated_part_cost"] = float(row["estimated_part_cost"])
    result["estimated_labor_minutes"] = int(row["estimated_labor_minutes"])
    return result


def delete_pricing_rule(rule_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM pricing_rules_catalog WHERE id = ?",
            (rule_id,),
        )
        connection.commit()
        return cursor.rowcount > 0


def get_pricing_rule_suggestion(brand: str, model: str, issue_type: str) -> dict | None:
    normalized_brand = brand.strip()
    normalized_model = model.strip()
    normalized_issue = issue_type.strip()
    if not normalized_brand or not normalized_model or not normalized_issue:
        return None

    with get_connection() as connection:
        row = connection.execute(
            f"""
            {_pricing_rules_base_query()}
            WHERE r.active = 1
              AND b.name = ?
              AND m.name = ?
              AND i.name = ?
            ORDER BY r.updated_at DESC
            LIMIT 1
            """,
            (normalized_brand, normalized_model, normalized_issue),
        ).fetchone()

    if row is None:
        return None

    result = dict(row)
    result["active"] = bool(row["active"])
    result["standard_price"] = float(row["standard_price"])
    result["estimated_part_cost"] = float(row["estimated_part_cost"])
    result["estimated_labor_minutes"] = int(row["estimated_labor_minutes"])
    return result

def seed_status_workflow_rules(connection: sqlite3.Connection) -> None:
    existing = connection.execute("SELECT id FROM status_workflow_rules WHERE id = 1").fetchone()
    if existing:
        return
    connection.execute(
        """
        INSERT INTO status_workflow_rules (id, transitions_json, guardrails_json, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            1,
            json.dumps(build_default_status_workflow_transitions()),
            json.dumps(DEFAULT_STATUS_WORKFLOW_GUARDRAILS),
            utc_now(),
        ),
    )


def get_status_workflow_rules() -> dict:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT transitions_json, guardrails_json, updated_at
            FROM status_workflow_rules
            WHERE id = 1
            """
        ).fetchone()

    if row is None:
        return {
            "transitions": build_default_status_workflow_transitions(),
            "guardrails": DEFAULT_STATUS_WORKFLOW_GUARDRAILS.copy(),
            "updated_at": utc_now(),
        }

    try:
        transitions = json.loads(row["transitions_json"])
    except json.JSONDecodeError:
        transitions = build_default_status_workflow_transitions()
    try:
        guardrails = json.loads(row["guardrails_json"])
    except json.JSONDecodeError:
        guardrails = DEFAULT_STATUS_WORKFLOW_GUARDRAILS.copy()

    return {
        "transitions": transitions,
        "guardrails": guardrails,
        "updated_at": row["updated_at"],
    }


def update_status_workflow_rules(payload: dict) -> dict:
    existing = get_status_workflow_rules()
    next_transitions = payload.get("transitions", existing["transitions"])
    next_guardrails = {
        **DEFAULT_STATUS_WORKFLOW_GUARDRAILS,
        **existing.get("guardrails", {}),
        **payload.get("guardrails", {}),
    }

    if not isinstance(next_transitions, dict):
        raise ValueError("transitions must be an object")

    normalized: dict[str, list[str]] = {}
    for from_status, to_statuses in next_transitions.items():
        if not isinstance(from_status, str) or not from_status.strip():
            raise ValueError("Each transition key must be a non-empty status name")
        if not isinstance(to_statuses, list) or any(not isinstance(item, str) or not item.strip() for item in to_statuses):
            raise ValueError("Each transition value must be a list of non-empty status names")
        deduped = sorted({item.strip() for item in to_statuses})
        normalized[from_status.strip()] = deduped

    for from_status, to_statuses in normalized.items():
        for target in to_statuses:
            if target not in normalized:
                raise ValueError(
                    f"Transition target '{target}' from '{from_status}' is missing as a workflow status key"
                )

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO status_workflow_rules (id, transitions_json, guardrails_json, updated_at)
            VALUES (1, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                transitions_json = excluded.transitions_json,
                guardrails_json = excluded.guardrails_json,
                updated_at = excluded.updated_at
            """,
            (json.dumps(normalized), json.dumps(next_guardrails), utc_now()),
        )
        connection.commit()

    return get_status_workflow_rules()


def seed_loaner_agreement_defaults(connection: sqlite3.Connection) -> None:
    existing = connection.execute("SELECT id FROM loaner_agreement_defaults WHERE id = 1").fetchone()
    if existing:
        return
    connection.execute(
        """
        INSERT INTO loaner_agreement_defaults (
            id,
            responsibility_text,
            return_policy_text,
            signature_note_text,
            updated_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            1,
            DEFAULT_LOANER_AGREEMENT_DEFAULTS["responsibility_text"],
            DEFAULT_LOANER_AGREEMENT_DEFAULTS["return_policy_text"],
            DEFAULT_LOANER_AGREEMENT_DEFAULTS["signature_note_text"],
            utc_now(),
        ),
    )


def get_loaner_agreement_defaults() -> dict:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT responsibility_text, return_policy_text, signature_note_text, updated_at
            FROM loaner_agreement_defaults
            WHERE id = 1
            """
        ).fetchone()

    if row is None:
        return {**DEFAULT_LOANER_AGREEMENT_DEFAULTS, "updated_at": utc_now()}

    return {
        "responsibility_text": row["responsibility_text"],
        "return_policy_text": row["return_policy_text"],
        "signature_note_text": row["signature_note_text"],
        "updated_at": row["updated_at"],
    }


def update_loaner_agreement_defaults(payload: dict) -> dict:
    existing = get_loaner_agreement_defaults()
    next_values = {
        "responsibility_text": payload.get("responsibility_text", existing["responsibility_text"]),
        "return_policy_text": payload.get("return_policy_text", existing["return_policy_text"]),
        "signature_note_text": payload.get("signature_note_text", existing["signature_note_text"]),
    }

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO loaner_agreement_defaults (
                id,
                responsibility_text,
                return_policy_text,
                signature_note_text,
                updated_at
            ) VALUES (1, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                responsibility_text = excluded.responsibility_text,
                return_policy_text = excluded.return_policy_text,
                signature_note_text = excluded.signature_note_text,
                updated_at = excluded.updated_at
            """,
            (
                next_values["responsibility_text"],
                next_values["return_policy_text"],
                next_values["signature_note_text"],
                utc_now(),
            ),
        )
        connection.commit()

    return get_loaner_agreement_defaults()


def seed_notification_templates(connection: sqlite3.Connection) -> None:
    existing_count = connection.execute("SELECT COUNT(*) AS count FROM notification_templates").fetchone()["count"]
    if existing_count:
        return

    for template_key, template_data in DEFAULT_NOTIFICATION_TEMPLATES.items():
        connection.execute(
            """
            INSERT INTO notification_templates (
                template_key,
                template_name,
                description,
                template_text,
                placeholders_json,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                template_key,
                template_data["template_name"],
                template_data["description"],
                template_data["template_text"],
                json.dumps(template_data["placeholders"]),
                utc_now(),
            ),
        )
    connection.commit()


def get_twilio_settings() -> dict:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT account_sid, auth_token_ciphertext, phone_number, public_webhook_base_url, voicemail_greeting, voicemail_greeting_audio_url, created_at, updated_at
            FROM twilio_settings
            WHERE id = 1
            """
        ).fetchone()

    if row is None:
        return {
            "account_sid": None,
            "phone_number": None,
            "public_webhook_base_url": None,
            "voicemail_greeting": None,
            "voicemail_greeting_audio_url": None,
            "twilio_auth_token_set": False,
            "configured": False,
            "created_at": None,
            "updated_at": None,
        }

    return {
        "account_sid": row["account_sid"],
        "phone_number": row["phone_number"],
        "public_webhook_base_url": row["public_webhook_base_url"],
        "voicemail_greeting": row["voicemail_greeting"],
        "voicemail_greeting_audio_url": row["voicemail_greeting_audio_url"],
        "twilio_auth_token_set": bool(row["auth_token_ciphertext"]),
        "configured": bool(row["account_sid"] and row["auth_token_ciphertext"] and row["phone_number"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def update_twilio_settings(payload: dict) -> dict:
    existing = get_twilio_settings()
    auth_token = payload.get("auth_token")
    clear_auth_token = bool(payload.get("clear_auth_token"))

    if clear_auth_token:
        next_auth_token_ciphertext = None
    elif isinstance(auth_token, str) and auth_token.strip():
        next_auth_token_ciphertext = _encrypt_twilio_value(auth_token.strip())
    else:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT auth_token_ciphertext FROM twilio_settings WHERE id = 1"
            ).fetchone()
        next_auth_token_ciphertext = row["auth_token_ciphertext"] if row else None

    next_values = {
        "account_sid": payload.get("account_sid", existing["account_sid"]),
        "auth_token_ciphertext": next_auth_token_ciphertext,
        "phone_number": payload.get("phone_number", existing["phone_number"]),
        "public_webhook_base_url": payload.get("public_webhook_base_url", existing["public_webhook_base_url"]),
        "voicemail_greeting": payload.get("voicemail_greeting", existing["voicemail_greeting"]),
        "voicemail_greeting_audio_url": payload.get("voicemail_greeting_audio_url", existing["voicemail_greeting_audio_url"]),
    }

    with get_connection() as connection:
        current_row = connection.execute(
            "SELECT created_at FROM twilio_settings WHERE id = 1"
        ).fetchone()
        if current_row is None:
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
                """,
                (
                    next_values["account_sid"],
                    next_values["auth_token_ciphertext"],
                    next_values["phone_number"],
                    next_values["public_webhook_base_url"],
                    next_values["voicemail_greeting"],
                    next_values["voicemail_greeting_audio_url"],
                    utc_now(),
                    utc_now(),
                ),
            )
        else:
            connection.execute(
                """
                UPDATE twilio_settings
                SET account_sid = ?,
                    auth_token_ciphertext = ?,
                    phone_number = ?,
                    public_webhook_base_url = ?,
                    voicemail_greeting = ?,
                    voicemail_greeting_audio_url = ?,
                    updated_at = ?
                WHERE id = 1
                """,
                (
                    next_values["account_sid"],
                    next_values["auth_token_ciphertext"],
                    next_values["phone_number"],
                    next_values["public_webhook_base_url"],
                    next_values["voicemail_greeting"],
                    next_values["voicemail_greeting_audio_url"],
                    utc_now(),
                ),
            )
        connection.commit()

    return get_twilio_settings()


def clear_twilio_settings() -> dict:
    with get_connection() as connection:
        connection.execute("DELETE FROM twilio_settings WHERE id = 1")
        connection.commit()
    return get_twilio_settings()


def find_customer_by_phone(phone_number: str | None) -> dict | None:
    if not phone_number:
        return None

    normalized = phone_number.strip()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, full_name, primary_phone, alternate_phone, email, notes, created_at, updated_at
            FROM customers
            WHERE primary_phone = ? OR alternate_phone = ?
            ORDER BY id ASC
            LIMIT 1
            """,
            (normalized, normalized),
        ).fetchone()
    return row_to_dict(row)


def create_voicemail_record(payload: dict) -> dict:
    recording_sid = payload.get("recording_sid")
    if recording_sid:
        existing = None
        with get_connection() as connection:
            existing = connection.execute(
                "SELECT id FROM voicemail_records WHERE recording_sid = ? LIMIT 1",
                (recording_sid,),
            ).fetchone()
        if existing is not None:
            return update_voicemail_record(int(existing["id"]), payload) or {}

    customer = find_customer_by_phone(payload.get("caller_number"))
    customer_id = payload.get("customer_id") or (customer["id"] if customer else None)
    timestamp = payload.get("created_at") or utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO voicemail_records (
                caller_number,
                called_number,
                call_sid,
                recording_sid,
                recording_url,
                recording_duration_seconds,
                transcription_text,
                notes,
                status,
                customer_id,
                ticket_id,
                listened_at,
                archived_at,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("caller_number"),
                payload.get("called_number"),
                payload.get("call_sid"),
                payload.get("recording_sid"),
                payload.get("recording_url"),
                payload.get("recording_duration_seconds"),
                payload.get("transcription_text"),
                payload.get("notes"),
                payload.get("status", "new"),
                customer_id,
                payload.get("ticket_id"),
                payload.get("listened_at"),
                payload.get("archived_at"),
                timestamp,
                timestamp,
            ),
        )
        connection.commit()
        row = connection.execute(
            """
            SELECT voicemail_records.*, customers.full_name AS customer_name, customers.primary_phone AS customer_phone
            FROM voicemail_records
            LEFT JOIN customers ON customers.id = voicemail_records.customer_id
            WHERE voicemail_records.id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return row_to_dict(row) or {}


def list_voicemail_records() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT voicemail_records.*, customers.full_name AS customer_name, customers.primary_phone AS customer_phone
            FROM voicemail_records
            LEFT JOIN customers ON customers.id = voicemail_records.customer_id
            ORDER BY voicemail_records.created_at DESC, voicemail_records.id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_voicemail_record(voicemail_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT voicemail_records.*, customers.full_name AS customer_name, customers.primary_phone AS customer_phone
            FROM voicemail_records
            LEFT JOIN customers ON customers.id = voicemail_records.customer_id
            WHERE voicemail_records.id = ?
            """,
            (voicemail_id,),
        ).fetchone()
    return row_to_dict(row)


def update_voicemail_record(voicemail_id: int, payload: dict) -> dict | None:
    existing = get_voicemail_record(voicemail_id)
    if existing is None:
        return None

    next_notes = existing.get("notes") or ""
    note = payload.get("note")
    if isinstance(note, str) and note.strip():
        stamp = utc_now()
        addition = f"[{stamp}] {note.strip()}"
        next_notes = f"{next_notes}\n{addition}".strip() if next_notes else addition

    next_status = payload.get("status", existing.get("status", "new"))
    updated_at = utc_now()
    if next_status == "listened" and existing.get("listened_at") is None:
        listened_at = updated_at
    else:
        listened_at = existing.get("listened_at")
    if next_status == "archived" and existing.get("archived_at") is None:
        archived_at = updated_at
    else:
        archived_at = existing.get("archived_at")

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE voicemail_records
            SET customer_id = ?,
                ticket_id = ?,
                notes = ?,
                status = ?,
                listened_at = ?,
                archived_at = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                payload.get("customer_id", existing.get("customer_id")),
                payload.get("ticket_id", existing.get("ticket_id")),
                next_notes,
                next_status,
                listened_at,
                archived_at,
                updated_at,
                voicemail_id,
            ),
        )
        connection.commit()

    return get_voicemail_record(voicemail_id)


def delete_voicemail_record(voicemail_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM voicemail_records WHERE id = ?",
            (voicemail_id,),
        )
        connection.commit()
    return bool(cursor.rowcount)


def get_decrypted_twilio_auth_token() -> str | None:
    row = get_twilio_settings()
    if not row.get("twilio_auth_token_set"):
        return None

    with get_connection() as connection:
        record = connection.execute(
            "SELECT auth_token_ciphertext FROM twilio_settings WHERE id = 1"
        ).fetchone()
    if record is None:
        return None
    return _decrypt_twilio_value(record["auth_token_ciphertext"])


def seed_operational_records(connection: sqlite3.Connection) -> None:
    timestamp = utc_now()

    def customer_id_by_name(full_name: str, phone: str | None = None) -> int | None:
        row = connection.execute(
            """
            SELECT id
            FROM customers
            WHERE full_name = ?
              AND COALESCE(primary_phone, '') = COALESCE(?, '')
            ORDER BY id ASC
            LIMIT 1
            """,
            (full_name, phone),
        ).fetchone()
        return int(row[0]) if row is not None else None

    def create_customer(full_name: str, phone: str | None = None, notes: str | None = None) -> int:
        existing_id = customer_id_by_name(full_name, phone)
        if existing_id is not None:
            return existing_id
        cursor = connection.execute(
            """
            INSERT INTO customers (full_name, primary_phone, alternate_phone, email, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (full_name, phone, None, None, notes, timestamp, timestamp),
        )
        return int(cursor.lastrowid)

    def sync_customer_timestamps(full_name: str, phone: str | None, created_at: str, updated_at: str) -> None:
        customer_id = customer_id_by_name(full_name, phone)
        if customer_id is None:
            return
        connection.execute(
            """
            UPDATE customers
            SET created_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (created_at, updated_at, customer_id),
        )

    def ticket_exists(customer_id: int, issue_category: str, device_label: str) -> bool:
        row = connection.execute(
            """
            SELECT id
            FROM repair_tickets
            WHERE customer_id = ?
              AND issue_category = ?
              AND COALESCE(device_model_text_override, '') = ?
            LIMIT 1
            """,
            (customer_id, issue_category, device_label),
        ).fetchone()
        return row is not None

    def create_ticket_record(payload: dict) -> int:
        cursor = connection.execute(
            """
            INSERT INTO repair_tickets (
                ticket_number,
                customer_id,
                device_model_id,
                device_model_text_override,
                carrier,
                sim_type,
                imei_serial,
                device_color,
                filter_status,
                issue_category,
                issue_description,
                condition_summary,
                water_damage_status,
                dropped_status,
                powers_on_status,
                charges_status,
                customer_approval_limit,
                must_call_before_repair,
                customer_prefers_replacement_if_high,
                estimated_price,
                final_price,
                payment_status,
                diagnostic_fee,
                status,
                priority,
                intake_staff,
                assigned_technician,
                intake_date,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["ticket_number"],
                payload["customer_id"],
                payload.get("device_model_id"),
                payload.get("device_model_text_override"),
                payload.get("carrier"),
                payload.get("sim_type"),
                payload.get("imei_serial"),
                payload.get("device_color"),
                payload.get("filter_status"),
                payload["issue_category"],
                payload.get("issue_description"),
                payload.get("condition_summary"),
                payload.get("water_damage_status", "unknown"),
                payload.get("dropped_status", "unknown"),
                payload.get("powers_on_status", "unknown"),
                payload.get("charges_status", "unknown"),
                payload.get("customer_approval_limit"),
                int(bool(payload.get("must_call_before_repair"))),
                int(bool(payload.get("customer_prefers_replacement_if_high"))),
                payload.get("estimated_price"),
                payload.get("final_price"),
                payload.get("payment_status", "unpaid"),
                payload.get("diagnostic_fee", 0),
                payload.get("status", "New Intake"),
                payload.get("priority", "normal"),
                payload.get("intake_staff"),
                payload.get("assigned_technician"),
                payload.get("intake_date", timestamp),
                payload.get("created_at", timestamp),
                payload.get("updated_at", timestamp),
            ),
        )
        return int(cursor.lastrowid)

    yossi_weiss_id = create_customer("Yossi Weiss", None, "Wonder phone touchpad replacement; customer supplied part")
    sync_customer_timestamps("Yossi Weiss", None, "2026-05-07T09:00:00Z", "2026-05-07T09:20:00Z")
    if not ticket_exists(yossi_weiss_id, "Touchpad replacement", "Wonder phone"):
        ticket_id = create_ticket_record(
            {
                "ticket_number": "TR-OPS-20260507-01",
                "customer_id": yossi_weiss_id,
                "device_model_text_override": "Wonder phone",
                "issue_category": "Touchpad replacement",
                "issue_description": "Touchpad replacement using customer supplied part.",
                "condition_summary": "Customer supplied part.",
                "final_price": 30,
                "payment_status": "unpaid",
                "status": "Picked Up / Closed",
                "intake_staff": "Mattis",
                "assigned_technician": "Mattis",
                "intake_date": "2026-05-07T09:00:00Z",
                "created_at": "2026-05-07T09:00:00Z",
                "updated_at": "2026-05-07T09:20:00Z",
            }
        )
        connection.executemany(
            """
            INSERT INTO ticket_status_history (ticket_id, old_status, new_status, changed_by, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (ticket_id, None, "New Intake", "Mattis", "Ticket created", "2026-05-07T09:00:00Z"),
                (ticket_id, "New Intake", "Picked Up / Closed", "Mattis", "Touchpad replacement completed with customer supplied part. Payment remains unpaid.", "2026-05-07T09:20:00Z"),
            ],
        )
        connection.executemany(
            """
            INSERT INTO ticket_notes (ticket_id, note_type, body, created_by, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (ticket_id, "front_desk", "Touchpad replacement. Customer supplied part. Around 20 minutes. Charge $30. Payment status unpaid.", "Mattis", "2026-05-07T09:05:00Z"),
                (ticket_id, "technician", "Completed replacement and tested touch input before release.", "Mattis", "2026-05-07T09:18:00Z"),
            ],
        )

    yossi_toder_id = create_customer("Yossi Toder", "732-664-1835", "SIM reader damage; declined expensive repair")
    sync_customer_timestamps("Yossi Toder", "732-664-1835", "2026-05-13T10:00:00Z", "2026-05-13T10:30:00Z")
    if not ticket_exists(yossi_toder_id, "SIM card not reading", "Alcatel 4044T"):
        ticket_id = create_ticket_record(
            {
                "ticket_number": "TR-OPS-20260513-01",
                "customer_id": yossi_toder_id,
                "device_model_text_override": "Alcatel 4044T",
                "issue_category": "SIM card not reading",
                "issue_description": "Device does not read SIM card; SIM reader appears heavily damaged.",
                "condition_summary": "SIM reader looked heavily damaged.",
                "payment_status": "unpaid",
                "status": "Customer Declined",
                "intake_staff": "Mattis",
                "assigned_technician": "Mattis",
                "intake_date": "2026-05-13T10:00:00Z",
                "created_at": "2026-05-13T10:00:00Z",
                "updated_at": "2026-05-13T10:30:00Z",
            }
        )
        connection.executemany(
            """
            INSERT INTO ticket_status_history (ticket_id, old_status, new_status, changed_by, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (ticket_id, None, "New Intake", "Mattis", "Ticket created", "2026-05-13T10:00:00Z"),
                (ticket_id, "New Intake", "Needs Diagnosis", "Mattis", "SIM reader looked heavily damaged.", "2026-05-13T10:15:00Z"),
                (ticket_id, "Needs Diagnosis", "Customer Declined", "Mattis", "Adjusted SIM reader and tested with SIM card. Device still did not read SIM card. Customer declined expensive/complicated repair.", "2026-05-13T10:30:00Z"),
            ],
        )
        connection.executemany(
            """
            INSERT INTO ticket_notes (ticket_id, note_type, body, created_by, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (ticket_id, "front_desk", "Issue: not reading SIM card. Customer does not want expensive or complicated repair.", "Mattis", "2026-05-13T10:05:00Z"),
                (ticket_id, "technician", "Adjusted SIM reader and tested with SIM card. Device still did not read SIM card.", "Mattis", "2026-05-13T10:20:00Z"),
            ],
        )

    hours_seed = [
        (yossi_weiss_id, "Mattis", "2026-05-07", 1.5, "Wonder phone touchpad replacement and testing"),
        (None, "Mattis", "2026-05-10", 3.3333, "General repair queue and bench work"),
        (None, "Mattis", "2026-05-11", 0.0, "No repair work logged"),
        (yossi_toder_id, "Mattis", "2026-05-13", 0.5, "SIM reader diagnosis and testing"),
        (None, "Mattis", "2026-05-14", 0.5, "Pickup prep and cleanup"),
        (None, "Mattis", "2026-05-24", 1.0, "General repair time"),
    ]
    for ticket_id, technician, work_date, hours_worked, work_description in hours_seed:
        existing = connection.execute(
            """
            SELECT id
            FROM technician_hours
            WHERE technician = ? AND work_date = ? AND COALESCE(ticket_id, 0) = COALESCE(?, 0)
              AND COALESCE(work_description, '') = COALESCE(?, '')
            LIMIT 1
            """,
            (technician, work_date, ticket_id, work_description),
        ).fetchone()
        if existing is None:
            connection.execute(
                """
                INSERT INTO technician_hours (ticket_id, technician, work_date, hours_worked, work_description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (ticket_id, technician, work_date, hours_worked, work_description, timestamp, timestamp),
            )

    purchase_row = connection.execute(
        """
        SELECT id
        FROM inventory_purchases
        WHERE purchase_date = ? AND total_cost = ?
        LIMIT 1
        """,
        ("2026-05-13", 770),
    ).fetchone()
    if purchase_row is None:
        cursor = connection.execute(
            """
            INSERT INTO inventory_purchases (purchase_date, vendor, reference_number, total_cost, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "2026-05-13",
                None,
                "OPS-20260513",
                770,
                "Existing operational device acquisition batch",
                timestamp,
                timestamp,
            ),
        )
        purchase_id = int(cursor.lastrowid)
        connection.executemany(
            """
            INSERT INTO inventory_purchase_items (
                purchase_id, item_type, manufacturer, item_name, quantity,
                estimated_unit_cost, line_total, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (purchase_id, "device", "Kyocera", "Kyocera E4610", 6, 90, 540, None, timestamp, timestamp),
                (purchase_id, "device", "Kyocera", "Kyocera E4810", 3, 60, 180, None, timestamp, timestamp),
                (purchase_id, "device", "LG", "LG Classic", 2, 25, 50, None, timestamp, timestamp),
            ],
        )

    connection.commit()


def seed_operational_records(connection: sqlite3.Connection) -> None:
    from app.real_seed_data import sync_real_customer_job_data

    sync_real_customer_job_data(connection, replace_existing=False)


def get_notification_templates() -> dict:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, template_key, template_name, description, template_text, placeholders_json, updated_at
            FROM notification_templates
            ORDER BY template_key
            """
        ).fetchall()

    templates = {}
    for row in rows:
        templates[row["template_key"]] = {
            "id": row["id"],
            "template_key": row["template_key"],
            "template_name": row["template_name"],
            "description": row["description"],
            "template_text": row["template_text"],
            "placeholders": json.loads(row["placeholders_json"]),
            "updated_at": row["updated_at"],
        }

    return templates


def update_notification_templates(payload: dict) -> dict:
    with get_connection() as connection:
        for template_key, template_data in payload.items():
            connection.execute(
                """
                UPDATE notification_templates
                SET template_text = ?, updated_at = ?
                WHERE template_key = ?
                """,
                (template_data.get("template_text"), utc_now(), template_key),
            )
        connection.commit()

    return get_notification_templates()


def get_repair_category(repair_category_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, name, description, default_policy, requires_soldering
            FROM repair_categories
            WHERE id = ?
            """,
            (repair_category_id,),
        ).fetchone()
    return row_to_dict(row)


def calculate_pricing(payload: dict) -> dict:
    defaults = get_pricing_defaults()
    part_cost = float(payload.get("part_cost", 0))
    labor_minutes = int(payload.get("labor_minutes", 0))
    difficulty_level = int(payload.get("difficulty_level", 1))
    risk_level = int(payload.get("risk_level", 1))
    base_labor_rate = float(payload.get("base_labor_rate_per_hour", defaults["base_labor_rate_per_hour"]))
    part_markup = float(payload.get("part_markup_percent", defaults["part_markup_percent"]))
    minimum_labor = float(payload.get("minimum_labor_charge", defaults["minimum_labor_charge"]))
    diagnostic_fee = float(payload.get("diagnostic_fee", defaults["diagnostic_fee"]))
    rush_fee = float(payload.get("rush_fee", 0))
    discount = float(payload.get("discount", 0))

    part_charge = part_cost * (1 + part_markup)
    labor_base = max(minimum_labor, (labor_minutes / 60) * base_labor_rate)
    adjusted_labor = labor_base * DIFFICULTY_MULTIPLIERS[difficulty_level] * RISK_MULTIPLIERS[risk_level]
    raw_price = part_charge + adjusted_labor + diagnostic_fee + rush_fee - discount
    customer_price = round_customer_price(raw_price)

    warnings: list[str] = []
    requires_soldering = False

    repair_category_id = payload.get("repair_category_id")
    if repair_category_id:
        category = get_repair_category(int(repair_category_id))
        requires_soldering = bool(category and category.get("requires_soldering"))
        if requires_soldering:
            warnings.append("Selected repair category requires soldering and is not supported in standard workflow.")

    ticket_id = payload.get("ticket_id")
    if ticket_id:
        ticket = get_ticket(int(ticket_id))
        if ticket and ticket.get("customer_approval_limit") is not None and customer_price > float(ticket["customer_approval_limit"]):
            warnings.append("Estimated price exceeds customer approval limit. Customer approval is required before repair.")

    replacement_value = payload.get("estimated_replacement_value")
    if replacement_value is not None and float(replacement_value) > 0:
        if customer_price > float(replacement_value) * 0.6:
            warnings.append("Repair may not be cost-effective versus replacement value.")

    return {
        "part_charge": round(part_charge, 2),
        "labor_base": round(labor_base, 2),
        "adjusted_labor": round(adjusted_labor, 2),
        "raw_price": round(raw_price, 2),
        "customer_price": round(customer_price, 2),
        "requires_soldering": requires_soldering,
        "warnings": warnings,
    }


def create_customer(payload: dict) -> dict:
    timestamp = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO customers (
                full_name,
                primary_phone,
                alternate_phone,
                email,
                notes,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["full_name"],
                payload.get("primary_phone"),
                payload.get("alternate_phone"),
                payload.get("email"),
                payload.get("notes"),
                timestamp,
                timestamp,
            ),
        )
        connection.commit()
        return get_customer(cursor.lastrowid)


def list_customers(search: str | None = None) -> list[dict]:
    where_clause = ""
    parameters: tuple = ()
    if search:
        where_clause = "WHERE full_name LIKE ? OR primary_phone LIKE ? OR alternate_phone LIKE ?"
        search_pattern = f"%{search}%"
        parameters = (search_pattern, search_pattern, search_pattern)

    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT id, full_name, primary_phone, alternate_phone, email, notes, created_at, updated_at
            FROM customers
            {where_clause}
            ORDER BY updated_at DESC, id DESC
            """,
            parameters,
        ).fetchall()
    return [dict(row) for row in rows]


def get_customer(customer_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, full_name, primary_phone, alternate_phone, email, notes, created_at, updated_at
            FROM customers
            WHERE id = ?
            """,
            (customer_id,),
        ).fetchone()
    return row_to_dict(row)


def update_customer(customer_id: int, payload: dict) -> dict | None:
    existing_customer = get_customer(customer_id)
    if existing_customer is None:
        return None

    updated_customer = {**existing_customer, **payload, "updated_at": utc_now()}
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE customers
            SET full_name = ?,
                primary_phone = ?,
                alternate_phone = ?,
                email = ?,
                notes = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                updated_customer["full_name"],
                updated_customer.get("primary_phone"),
                updated_customer.get("alternate_phone"),
                updated_customer.get("email"),
                updated_customer.get("notes"),
                updated_customer["updated_at"],
                customer_id,
            ),
        )
        connection.commit()
    return get_customer(customer_id)


def ensure_customer_exists(customer_id: int) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id FROM customers WHERE id = ?",
            (customer_id,),
        ).fetchone()
    return row is not None


def ensure_supported_model_exists(model_id: int | None) -> bool:
    if model_id is None:
        return True
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id FROM supported_device_models WHERE id = ?",
            (model_id,),
        ).fetchone()
    return row is not None


def generate_ticket_number(connection: sqlite3.Connection) -> str:
    count = connection.execute(
        "SELECT COUNT(*) AS count FROM repair_tickets"
    ).fetchone()["count"]
    return f"TR-{count + 1:05d}"


def create_ticket(payload: dict) -> dict:
    timestamp = utc_now()
    with get_connection() as connection:
        ticket_number = generate_ticket_number(connection)
        cursor = connection.execute(
            """
            INSERT INTO repair_tickets (
                ticket_number,
                customer_id,
                device_model_id,
                device_model_text_override,
                carrier,
                sim_type,
                imei_serial,
                device_color,
                filter_status,
                issue_category,
                issue_description,
                condition_summary,
                water_damage_status,
                dropped_status,
                powers_on_status,
                charges_status,
                customer_approval_limit,
                must_call_before_repair,
                customer_prefers_replacement_if_high,
                estimated_price,
                final_price,
                payment_status,
                diagnostic_fee,
                status,
                priority,
                intake_staff,
                assigned_technician,
                intake_date,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_number,
                payload["customer_id"],
                payload.get("device_model_id"),
                payload.get("device_model_text_override"),
                payload.get("carrier"),
                payload.get("sim_type"),
                payload.get("imei_serial"),
                payload.get("device_color"),
                payload.get("filter_status"),
                payload["issue_category"],
                payload.get("issue_description"),
                payload.get("condition_summary"),
                payload.get("water_damage_status", "unknown"),
                payload.get("dropped_status", "unknown"),
                payload.get("powers_on_status", "unknown"),
                payload.get("charges_status", "unknown"),
                payload.get("customer_approval_limit"),
                int(bool(payload.get("must_call_before_repair"))),
                int(bool(payload.get("customer_prefers_replacement_if_high"))),
                payload.get("estimated_price"),
                payload.get("final_price"),
                payload.get("payment_status", "unpaid"),
                payload.get("diagnostic_fee", 0),
                payload.get("status", "New Intake"),
                payload.get("priority", "normal"),
                payload.get("intake_staff"),
                payload.get("assigned_technician"),
                timestamp,
                timestamp,
                timestamp,
            ),
        )
        ticket_id = cursor.lastrowid
        connection.execute(
            """
            INSERT INTO ticket_status_history (ticket_id, old_status, new_status, changed_by, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                None,
                payload.get("status", "New Intake"),
                payload.get("intake_staff"),
                "Ticket created",
                timestamp,
            ),
        )
        intake_note = payload.get("intake_note")
        if intake_note:
            connection.execute(
                """
                INSERT INTO ticket_notes (ticket_id, note_type, body, created_by, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (ticket_id, "front_desk", intake_note, payload.get("intake_staff"), timestamp),
            )
        connection.commit()
    return get_ticket(ticket_id)


def list_tickets(status: str | None = None, search: str | None = None) -> list[dict]:
    filters: list[str] = []
    parameters: list[str] = []
    if status:
        filters.append("repair_tickets.status = ?")
        parameters.append(status)
    if search:
        filters.append(
            "(repair_tickets.ticket_number LIKE ? OR customers.full_name LIKE ? OR customers.primary_phone LIKE ? OR repair_tickets.issue_category LIKE ? OR supported_device_models.model_name LIKE ? OR repair_tickets.device_model_text_override LIKE ?)"
        )
        search_pattern = f"%{search}%"
        parameters.extend([search_pattern] * 6)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT repair_tickets.*, customers.full_name AS customer_name,
                   COALESCE(customers.primary_phone, customers.alternate_phone) AS customer_phone,
                   supported_device_models.manufacturer,
                   supported_device_models.model_name
            FROM repair_tickets
            INNER JOIN customers ON customers.id = repair_tickets.customer_id
            LEFT JOIN supported_device_models ON supported_device_models.id = repair_tickets.device_model_id
            {where_clause}
            ORDER BY repair_tickets.updated_at DESC, repair_tickets.id DESC
            """,
            tuple(parameters),
        ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["device_label"] = build_device_label(row)
        items.append(item)
    return items


def get_ticket(ticket_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT repair_tickets.*, customers.full_name AS customer_name,
                   customers.primary_phone AS customer_phone,
                   customers.alternate_phone AS customer_alternate_phone,
                   supported_device_models.manufacturer,
                   supported_device_models.model_name
            FROM repair_tickets
            INNER JOIN customers ON customers.id = repair_tickets.customer_id
            LEFT JOIN supported_device_models ON supported_device_models.id = repair_tickets.device_model_id
            WHERE repair_tickets.id = ?
            """,
            (ticket_id,),
        ).fetchone()
    if row is None:
        return None

    item = dict(row)
    item["device_label"] = build_device_label(row)
    item["must_call_before_repair"] = bool(item["must_call_before_repair"])
    item["customer_prefers_replacement_if_high"] = bool(item["customer_prefers_replacement_if_high"])
    item["history"] = list_ticket_history(ticket_id)
    item["notes"] = list_ticket_notes(ticket_id)
    item["repair_actions"] = list_repair_actions(ticket_id)
    return item


def update_ticket(ticket_id: int, payload: dict) -> dict | None:
    existing_ticket = get_ticket(ticket_id)
    if existing_ticket is None:
        return None

    updated_ticket = {**existing_ticket, **payload, "updated_at": utc_now()}
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE repair_tickets
            SET device_model_id = ?,
                device_model_text_override = ?,
                carrier = ?,
                sim_type = ?,
                imei_serial = ?,
                device_color = ?,
                filter_status = ?,
                issue_category = ?,
                issue_description = ?,
                condition_summary = ?,
                water_damage_status = ?,
                dropped_status = ?,
                powers_on_status = ?,
                charges_status = ?,
                customer_approval_limit = ?,
                must_call_before_repair = ?,
                customer_prefers_replacement_if_high = ?,
                estimated_price = ?,
                final_price = ?,
                payment_status = ?,
                diagnostic_fee = ?,
                status = ?,
                priority = ?,
                intake_staff = ?,
                assigned_technician = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                updated_ticket.get("device_model_id"),
                updated_ticket.get("device_model_text_override"),
                updated_ticket.get("carrier"),
                updated_ticket.get("sim_type"),
                updated_ticket.get("imei_serial"),
                updated_ticket.get("device_color"),
                updated_ticket.get("filter_status"),
                updated_ticket["issue_category"],
                updated_ticket.get("issue_description"),
                updated_ticket.get("condition_summary"),
                updated_ticket.get("water_damage_status", "unknown"),
                updated_ticket.get("dropped_status", "unknown"),
                updated_ticket.get("powers_on_status", "unknown"),
                updated_ticket.get("charges_status", "unknown"),
                updated_ticket.get("customer_approval_limit"),
                int(bool(updated_ticket.get("must_call_before_repair"))),
                int(bool(updated_ticket.get("customer_prefers_replacement_if_high"))),
                updated_ticket.get("estimated_price"),
                updated_ticket.get("final_price"),
                updated_ticket.get("payment_status", "unpaid"),
                updated_ticket.get("diagnostic_fee", 0),
                updated_ticket.get("status", "New Intake"),
                updated_ticket.get("priority", "normal"),
                updated_ticket.get("intake_staff"),
                updated_ticket.get("assigned_technician"),
                updated_ticket["updated_at"],
                ticket_id,
            ),
        )
        connection.commit()
    return get_ticket(ticket_id)


def add_ticket_status_history(ticket_id: int, payload: dict) -> dict:
    existing_ticket = get_ticket(ticket_id)
    previous_status = existing_ticket["status"]
    timestamp = utc_now()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO ticket_status_history (ticket_id, old_status, new_status, changed_by, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                previous_status,
                payload["new_status"],
                payload.get("changed_by"),
                payload.get("note"),
                timestamp,
            ),
        )
        connection.execute(
            "UPDATE repair_tickets SET status = ?, updated_at = ? WHERE id = ?",
            (payload["new_status"], timestamp, ticket_id),
        )
        connection.commit()
    return list_ticket_history(ticket_id)[-1]


def list_ticket_history(ticket_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, ticket_id, old_status, new_status, changed_by, note, created_at
            FROM ticket_status_history
            WHERE ticket_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (ticket_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def add_ticket_note(ticket_id: int, payload: dict) -> dict:
    timestamp = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO ticket_notes (ticket_id, note_type, body, created_by, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                payload["note_type"],
                payload["body"],
                payload.get("created_by"),
                timestamp,
            ),
        )
        connection.execute(
            "UPDATE repair_tickets SET updated_at = ? WHERE id = ?",
            (timestamp, ticket_id),
        )
        connection.commit()

    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, ticket_id, note_type, body, created_by, created_at FROM ticket_notes WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return dict(row)


def list_ticket_notes(ticket_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, ticket_id, note_type, body, created_by, created_at
            FROM ticket_notes
            WHERE ticket_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (ticket_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_customer_tickets(customer_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT repair_tickets.*, customers.full_name AS customer_name,
                   COALESCE(customers.primary_phone, customers.alternate_phone) AS customer_phone,
                   supported_device_models.manufacturer,
                   supported_device_models.model_name
            FROM repair_tickets
            INNER JOIN customers ON customers.id = repair_tickets.customer_id
            LEFT JOIN supported_device_models ON supported_device_models.id = repair_tickets.device_model_id
            WHERE repair_tickets.customer_id = ?
            ORDER BY repair_tickets.updated_at DESC, repair_tickets.id DESC
            """,
            (customer_id,),
        ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["device_label"] = build_device_label(row)
        items.append(item)
    return items


def list_repair_actions(ticket_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT repair_actions.id,
                   repair_actions.ticket_id,
                   repair_actions.repair_category_id,
                   repair_categories.name AS repair_category_name,
                   repair_actions.action_description,
                   repair_actions.part_cost,
                   repair_actions.labor_minutes,
                   repair_actions.difficulty_level,
                   repair_actions.risk_level,
                   repair_actions.calculated_price,
                   repair_actions.final_price,
                   repair_actions.status,
                   repair_actions.performed_by,
                   repair_actions.performed_at,
                   COALESCE(repair_categories.requires_soldering, 0) AS requires_soldering
            FROM repair_actions
            LEFT JOIN repair_categories ON repair_categories.id = repair_actions.repair_category_id
            WHERE repair_actions.ticket_id = ?
            ORDER BY repair_actions.id DESC
            """,
            (ticket_id,),
        ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["requires_soldering"] = bool(item["requires_soldering"])
        items.append(item)
    return items


def add_repair_action(ticket_id: int, payload: dict) -> dict:
    if get_ticket(ticket_id) is None:
        raise ValueError("Ticket not found")

    pricing_input = {
        "ticket_id": ticket_id,
        "repair_category_id": payload["repair_category_id"],
        "part_cost": payload.get("part_cost", 0),
        "labor_minutes": payload.get("labor_minutes", 0),
        "difficulty_level": payload.get("difficulty_level", 1),
        "risk_level": payload.get("risk_level", 1),
        "diagnostic_fee": payload.get("diagnostic_fee", 0),
        "rush_fee": payload.get("rush_fee", 0),
        "discount": payload.get("discount", 0),
        "estimated_replacement_value": payload.get("estimated_replacement_value"),
    }
    pricing = calculate_pricing(pricing_input)
    if pricing["requires_soldering"]:
        raise ValueError("Repair action requires soldering and cannot be added to standard workflow")

    timestamp = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO repair_actions (
                ticket_id,
                repair_category_id,
                action_description,
                part_cost,
                labor_minutes,
                difficulty_level,
                risk_level,
                calculated_price,
                final_price,
                status,
                performed_by,
                performed_at,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                payload["repair_category_id"],
                payload.get("action_description"),
                payload.get("part_cost", 0),
                payload.get("labor_minutes", 0),
                payload.get("difficulty_level", 1),
                payload.get("risk_level", 1),
                pricing["customer_price"],
                payload.get("final_price"),
                payload.get("status", "planned"),
                payload.get("performed_by"),
                payload.get("performed_at"),
                timestamp,
            ),
        )
        connection.execute(
            "UPDATE repair_tickets SET updated_at = ? WHERE id = ?",
            (timestamp, ticket_id),
        )
        connection.commit()
        action_id = cursor.lastrowid

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT repair_actions.id,
                   repair_actions.ticket_id,
                   repair_actions.repair_category_id,
                   repair_categories.name AS repair_category_name,
                   repair_actions.action_description,
                   repair_actions.part_cost,
                   repair_actions.labor_minutes,
                   repair_actions.difficulty_level,
                   repair_actions.risk_level,
                   repair_actions.calculated_price,
                   repair_actions.final_price,
                   repair_actions.status,
                   repair_actions.performed_by,
                   repair_actions.performed_at,
                   COALESCE(repair_categories.requires_soldering, 0) AS requires_soldering
            FROM repair_actions
            LEFT JOIN repair_categories ON repair_categories.id = repair_actions.repair_category_id
            WHERE repair_actions.id = ?
            """,
            (action_id,),
        ).fetchone()

    item = dict(row)
    item["requires_soldering"] = bool(item["requires_soldering"])
    return item


def create_loaner_phone(payload: dict) -> dict:
    timestamp = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO loaner_phones (
                loaner_code,
                manufacturer,
                model,
                carrier_compatibility,
                charger_type,
                sim_type,
                filter_status,
                condition_current,
                status,
                default_deposit,
                notes,
                active,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Available', ?, ?, 1, ?, ?)
            """,
            (
                payload["loaner_code"],
                payload.get("manufacturer"),
                payload["model"],
                payload.get("carrier_compatibility"),
                payload.get("charger_type"),
                payload.get("sim_type"),
                payload.get("filter_status"),
                payload.get("condition_current"),
                payload.get("default_deposit", 0),
                payload.get("notes"),
                timestamp,
                timestamp,
            ),
        )
        connection.commit()
    return get_loaner_phone(cursor.lastrowid)


def list_loaner_phones(status: str | None = None) -> list[dict]:
    where_clause = "WHERE active = 1"
    parameters: tuple = ()
    if status:
        where_clause += " AND status = ?"
        parameters = (status,)

    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT id, loaner_code, manufacturer, model, carrier_compatibility, charger_type,
                   sim_type, filter_status, condition_current, status, default_deposit,
                   notes, active, created_at, updated_at
            FROM loaner_phones
            {where_clause}
            ORDER BY loaner_code ASC
            """,
            parameters,
        ).fetchall()
    return [format_loaner_phone_row(dict(row)) for row in rows]


def get_loaner_phone(loaner_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, loaner_code, manufacturer, model, carrier_compatibility, charger_type,
                   sim_type, filter_status, condition_current, status, default_deposit,
                   notes, active, created_at, updated_at
            FROM loaner_phones
            WHERE id = ?
            """,
            (loaner_id,),
        ).fetchone()
    if row is None:
        return None
    return format_loaner_phone_row(dict(row))


def format_loaner_phone_row(item: dict) -> dict:
    item["active"] = bool(item["active"])
    return item


def update_loaner_phone(loaner_id: int, payload: dict) -> dict | None:
    existing_loaner = get_loaner_phone(loaner_id)
    if existing_loaner is None:
        return None

    updated_loaner = {**existing_loaner, **payload, "updated_at": utc_now()}
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE loaner_phones
            SET manufacturer = ?,
                model = ?,
                carrier_compatibility = ?,
                charger_type = ?,
                sim_type = ?,
                filter_status = ?,
                condition_current = ?,
                status = ?,
                default_deposit = ?,
                notes = ?,
                active = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                updated_loaner.get("manufacturer"),
                updated_loaner["model"],
                updated_loaner.get("carrier_compatibility"),
                updated_loaner.get("charger_type"),
                updated_loaner.get("sim_type"),
                updated_loaner.get("filter_status"),
                updated_loaner.get("condition_current"),
                updated_loaner.get("status", "Available"),
                updated_loaner.get("default_deposit", 0),
                updated_loaner.get("notes"),
                int(bool(updated_loaner.get("active", True))),
                updated_loaner["updated_at"],
                loaner_id,
            ),
        )
        connection.commit()
    return get_loaner_phone(loaner_id)


def has_active_loaner_checkout_for_ticket(ticket_id: int) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id FROM loaner_checkouts
            WHERE ticket_id = ? AND status = 'Checked Out'
            """,
            (ticket_id,),
        ).fetchone()
    return row is not None


def get_open_checkout_by_loaner(loaner_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM loaner_checkouts
            WHERE loaner_phone_id = ? AND status = 'Checked Out'
            ORDER BY id DESC
            LIMIT 1
            """,
            (loaner_id,),
        ).fetchone()
    return format_checkout_row(dict(row)) if row is not None else None


def format_checkout_row(item: dict) -> dict:
    item["charger_included"] = bool(item["charger_included"])
    item["charger_returned"] = to_bool(item["charger_returned"])
    item["sim_moved"] = bool(item["sim_moved"])
    item["outgoing_call_tested"] = bool(item["outgoing_call_tested"])
    item["incoming_call_tested"] = bool(item["incoming_call_tested"])
    item["agreement_signed"] = bool(item["agreement_signed"])
    return item


def checkout_loaner(loaner_id: int, payload: dict) -> dict | None:
    loaner = get_loaner_phone(loaner_id)
    if loaner is None:
        return None
    if loaner["status"] != "Available":
        raise ValueError("Loaner is not available")
    if not ensure_customer_exists(payload["customer_id"]):
        raise ValueError("Customer does not exist")
    if get_ticket(payload["ticket_id"]) is None:
        raise ValueError("Ticket does not exist")

    timestamp = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO loaner_checkouts (
                loaner_phone_id,
                ticket_id,
                customer_id,
                date_out,
                expected_return_date,
                condition_out,
                charger_included,
                sim_moved,
                outgoing_call_tested,
                incoming_call_tested,
                deposit_amount,
                agreement_signed,
                checkout_staff,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Checked Out')
            """,
            (
                loaner_id,
                payload["ticket_id"],
                payload["customer_id"],
                timestamp,
                payload.get("expected_return_date"),
                payload.get("condition_out"),
                int(bool(payload.get("charger_included"))),
                int(bool(payload.get("sim_moved"))),
                int(bool(payload.get("outgoing_call_tested"))),
                int(bool(payload.get("incoming_call_tested"))),
                payload.get("deposit_amount", loaner.get("default_deposit", 0)),
                int(bool(payload.get("agreement_signed"))),
                payload.get("checkout_staff"),
            ),
        )
        connection.execute(
            "UPDATE loaner_phones SET status = 'Checked Out', updated_at = ? WHERE id = ?",
            (timestamp, loaner_id),
        )
        connection.commit()

    return get_checkout(cursor.lastrowid)


def get_checkout(checkout_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM loaner_checkouts WHERE id = ?",
            (checkout_id,),
        ).fetchone()
    return format_checkout_row(dict(row)) if row is not None else None


def return_loaner(loaner_id: int, payload: dict) -> dict:
    open_checkout = get_open_checkout_by_loaner(loaner_id)
    if open_checkout is None:
        raise ValueError("No active checkout for this loaner")

    timestamp = utc_now()
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE loaner_checkouts
            SET date_returned = ?,
                condition_returned = ?,
                charger_returned = ?,
                deposit_refunded = ?,
                deposit_deducted = ?,
                deduction_reason = ?,
                return_staff = ?,
                status = 'Returned'
            WHERE id = ?
            """,
            (
                timestamp,
                payload.get("condition_returned"),
                None if payload.get("charger_returned") is None else int(bool(payload.get("charger_returned"))),
                payload.get("deposit_refunded", 0),
                payload.get("deposit_deducted", 0),
                payload.get("deduction_reason"),
                payload.get("return_staff"),
                open_checkout["id"],
            ),
        )
        connection.execute(
            "UPDATE loaner_phones SET status = ?, updated_at = ? WHERE id = ?",
            (payload.get("next_status", "Returned Needs Reset"), timestamp, loaner_id),
        )
        connection.commit()

    return get_checkout(open_checkout["id"])


def list_overdue_loaner_checkouts() -> list[dict]:
    now_iso = utc_now()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM loaner_checkouts
            WHERE status = 'Checked Out'
              AND expected_return_date IS NOT NULL
              AND expected_return_date < ?
            ORDER BY expected_return_date ASC
            """,
            (now_iso,),
        ).fetchall()
    return [format_checkout_row(dict(row)) for row in rows]


def get_loaner_alert_summary() -> dict:
    with get_connection() as connection:
        checked_out_count = connection.execute(
            "SELECT COUNT(*) AS count FROM loaner_checkouts WHERE status = 'Checked Out'"
        ).fetchone()["count"]
        overdue_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM loaner_checkouts
            WHERE status = 'Checked Out'
              AND expected_return_date IS NOT NULL
              AND expected_return_date < ?
            """,
            (utc_now(),),
        ).fetchone()["count"]
        missing_charger_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM loaner_checkouts
            WHERE status = 'Returned' AND charger_included = 1 AND (charger_returned = 0 OR charger_returned IS NULL)
            """
        ).fetchone()["count"]
        needs_reset_or_cleaning_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM loaner_phones
            WHERE status IN ('Returned Needs Reset', 'Returned Needs Cleaning')
            """
        ).fetchone()["count"]

    return {
        "checked_out_count": checked_out_count,
        "overdue_count": overdue_count,
        "missing_charger_count": missing_charger_count,
        "needs_reset_or_cleaning_count": needs_reset_or_cleaning_count,
    }


def get_dashboard_summary() -> dict:
    with get_connection() as connection:
        open_tickets_count = connection.execute(
            "SELECT COUNT(*) AS count FROM repair_tickets WHERE status != 'Picked Up / Closed'"
        ).fetchone()["count"]
    loaner_summary = get_loaner_alert_summary()
    return {
        "open_tickets_count": open_tickets_count,
        "checked_out_loaners_count": loaner_summary["checked_out_count"],
        "overdue_loaners_count": loaner_summary["overdue_count"],
    }


def close_ticket_with_guard(ticket_id: int, payload: dict) -> dict | None:
    existing_ticket = get_ticket(ticket_id)
    if existing_ticket is None:
        return None
    if has_active_loaner_checkout_for_ticket(ticket_id):
        raise ValueError("Cannot close ticket while loaner is still checked out")

    timestamp = utc_now()
    close_note = payload.get("note") or "Ticket closed"
    changed_by = payload.get("changed_by")

    with get_connection() as connection:
        final_price = payload.get("final_price", existing_ticket.get("final_price"))
        connection.execute(
            """
            UPDATE repair_tickets
            SET status = 'Picked Up / Closed',
                final_price = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (final_price, timestamp, ticket_id),
        )
        connection.execute(
            """
            INSERT INTO ticket_status_history (ticket_id, old_status, new_status, changed_by, note, created_at)
            VALUES (?, ?, 'Picked Up / Closed', ?, ?, ?)
            """,
            (ticket_id, existing_ticket["status"], changed_by, close_note, timestamp),
        )
        connection.commit()

    return {
        "ticket_id": ticket_id,
        "status": "Picked Up / Closed",
        "closed": True,
    }


# ============================================================================
# Phase 4: Technician Queue and Hours Logging
# ============================================================================


def get_technician_queue() -> dict[str, list[dict]]:
    """
    Group all open tickets by status for technician workflow.
    
    Queue priorities:
    1. Loaner Outstanding (customer has overdue loaner)
    2. Waiting for Parts (blocked on parts, needs follow-up)
    3. Customer Approval Needed (blocked on approval)
    4. New Intake (just arrived, needs triage)
    5. Needs Diagnosis (awaiting tech review)
    
    Returns dict with status keys and ticket lists.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                rt.id,
                rt.ticket_number,
                rt.customer_id,
                c.full_name AS customer_name,
                c.primary_phone AS customer_phone,
                sdm.manufacturer,
                sdm.model_name,
                rt.issue_category,
                rt.status,
                rt.customer_approval_limit,
                rt.assigned_technician,
                rt.intake_date,
                rt.created_at,
                CASE
                    WHEN EXISTS (
                        SELECT 1 FROM loaner_checkouts lc
                        WHERE lc.ticket_id = rt.id
                          AND lc.status = 'Checked Out'
                    ) THEN 'Loaner Outstanding'
                    WHEN rt.status IN ('Waiting for Parts', 'Customer Approval Needed', 'New Intake', 'Needs Diagnosis') THEN rt.status
                    ELSE NULL
                END AS queue_bucket
            FROM repair_tickets rt
            LEFT JOIN customers c ON c.id = rt.customer_id
            LEFT JOIN supported_device_models sdm ON sdm.id = rt.device_model_id
            WHERE rt.status NOT IN ('Picked Up / Closed', 'In Repair', 'Ready for Pickup')
            ORDER BY rt.created_at ASC
            """
        ).fetchall()

    queue = {
        "Loaner Outstanding": [],
        "Waiting for Parts": [],
        "Customer Approval Needed": [],
        "New Intake": [],
        "Needs Diagnosis": [],
    }

    for row in rows:
        ticket = dict(row)
        bucket = ticket.pop("queue_bucket", None)
        if bucket in queue:
            queue[bucket].append(ticket)
    
    return queue


def log_hours(payload: dict) -> dict:
    """
    Log technician hours for a given date and optional ticket.
    
    Args:
        payload: {
            "technician": "Bob",
            "work_date": "2026-05-07",
            "hours_worked": 1.5,
            "work_description": "Screen replacement",
            "ticket_id": 5 (optional)
        }
    
    Returns: Hours entry dict with id, created_at, updated_at
    """
    timestamp = utc_now()
    ticket_id = payload.get("ticket_id")
    raw_work_date = str(payload["work_date"]).strip()

    # Accept either YYYY-MM-DD or full ISO datetime and store normalized date only.
    if not raw_work_date:
        raise ValueError("work_date is required")
    try:
        if "T" in raw_work_date:
            parsed_work_date = datetime.fromisoformat(raw_work_date.replace("Z", "+00:00")).date().isoformat()
        else:
            parsed_work_date = raw_work_date[:10]
    except ValueError as exc:
        raise ValueError("work_date must be a valid date or ISO datetime") from exc
    
    # Validate ticket if provided
    if ticket_id:
        if get_ticket(ticket_id) is None:
            raise ValueError(f"Ticket {ticket_id} not found")
    
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO technician_hours (
                ticket_id,
                technician,
                work_date,
                hours_worked,
                work_description,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                payload["technician"],
                parsed_work_date,
                float(payload["hours_worked"]),
                payload.get("work_description"),
                timestamp,
                timestamp,
            ),
        )
        connection.commit()
    
    return get_hours_entry(cursor.lastrowid)


def get_hours_entry(hours_id: int) -> dict | None:
    """Get a single hours entry by ID."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, ticket_id, technician, DATE(work_date) AS work_date, hours_worked,
                   work_description, created_at, updated_at
            FROM technician_hours
            WHERE id = ?
            """,
            (hours_id,),
        ).fetchone()
    return row_to_dict(row)


def _format_clock_session(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None

    item = dict(row)
    start_time = datetime.fromisoformat(item["clocked_in_at"])
    end_time = datetime.fromisoformat(item["clocked_out_at"]) if item["clocked_out_at"] else datetime.now(UTC)
    elapsed_seconds = max(int((end_time - start_time).total_seconds()), 0)
    item["elapsed_seconds"] = elapsed_seconds
    item["elapsed_hours"] = round(elapsed_seconds / 3600, 2)
    return item


def get_active_clock_session(technician: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, ticket_id, technician, work_description, clocked_in_at,
                   clocked_out_at, status, created_at, updated_at
            FROM technician_clock_sessions
            WHERE technician = ? AND status = 'active' AND clocked_out_at IS NULL
            ORDER BY id DESC
            LIMIT 1
            """,
            (technician,),
        ).fetchone()
    return _format_clock_session(row)


def get_clock_session(session_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, ticket_id, technician, work_description, clocked_in_at,
                   clocked_out_at, status, created_at, updated_at
            FROM technician_clock_sessions
            WHERE id = ?
            """,
            (session_id,),
        ).fetchone()
    return _format_clock_session(row)


def clock_in_technician(payload: dict) -> dict:
    technician = payload["technician"].strip()
    if get_active_clock_session(technician) is not None:
        raise ValueError(f"{technician} already has an active clock session")

    ticket_id = payload.get("ticket_id")
    if ticket_id and get_ticket(ticket_id) is None:
        raise ValueError(f"Ticket {ticket_id} not found")

    timestamp = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO technician_clock_sessions (
                ticket_id,
                technician,
                work_description,
                clocked_in_at,
                clocked_out_at,
                status,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, NULL, 'active', ?, ?)
            """,
            (
                ticket_id,
                technician,
                payload.get("work_description"),
                timestamp,
                timestamp,
                timestamp,
            ),
        )
        connection.commit()
    return get_clock_session(cursor.lastrowid)


def clock_out_technician(payload: dict) -> dict:
    technician = payload["technician"].strip()
    active_session = get_active_clock_session(technician)
    if active_session is None:
        raise ValueError(f"No active clock session for {technician}")

    ticket_id = payload.get("ticket_id")
    if ticket_id is None:
        ticket_id = active_session.get("ticket_id")
    if ticket_id and get_ticket(ticket_id) is None:
        raise ValueError(f"Ticket {ticket_id} not found")

    work_description = payload.get("work_description") or active_session.get("work_description")
    clocked_out_at = utc_now()
    started_at = datetime.fromisoformat(active_session["clocked_in_at"])
    ended_at = datetime.fromisoformat(clocked_out_at)
    elapsed_seconds = max(int((ended_at - started_at).total_seconds()), 0)
    hours_worked = round(max(elapsed_seconds / 3600, 0.01), 2)

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE technician_clock_sessions
            SET ticket_id = ?,
                work_description = ?,
                clocked_out_at = ?,
                status = 'completed',
                updated_at = ?
            WHERE id = ?
            """,
            (
                ticket_id,
                work_description,
                clocked_out_at,
                clocked_out_at,
                active_session["id"],
            ),
        )
        connection.commit()

    hours_entry = log_hours(
        {
            "ticket_id": ticket_id,
            "technician": technician,
            "work_date": ended_at.date().isoformat(),
            "hours_worked": hours_worked,
            "work_description": work_description,
        }
    )
    return {
        "session": get_clock_session(active_session["id"]),
        "hours_entry": hours_entry,
    }


def list_hours(
    start_date: str | None = None,
    end_date: str | None = None,
    technician: str | None = None,
) -> list[dict]:
    """
    List hours entries with optional filters.
    
    Args:
        start_date: ISO date string (inclusive)
        end_date: ISO date string (inclusive)
        technician: Filter by technician name (exact match)
    
    Returns: List of hours entries
    """
    where_clauses = []
    parameters: list = []
    
    if start_date:
        where_clauses.append("DATE(work_date) >= DATE(?)")
        parameters.append(start_date)
    
    if end_date:
        where_clauses.append("DATE(work_date) <= DATE(?)")
        parameters.append(end_date)
    
    if technician:
        where_clauses.append("technician = ?")
        parameters.append(technician)
    
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT id, ticket_id, technician, DATE(work_date) AS work_date, hours_worked,
                   work_description, created_at, updated_at
            FROM technician_hours
            WHERE {where_clause}
            ORDER BY DATE(work_date) DESC, technician ASC, id DESC
            """,
            parameters,
        ).fetchall()
    return [dict(row) for row in rows]


def get_hours_summary(
    start_date: str | None = None,
    end_date: str | None = None,
    technician: str | None = None,
) -> dict:
    """
    Aggregate hours by technician and overall for a date range.
    
    Returns:
        {
            "by_technician": {"Bob": 8.5, "Jane": 6.5},
            "total_hours": 15.0,
            "date_range": {"start": "2026-05-01", "end": "2026-05-07"}
        }
    """
    where_clauses = []
    parameters: list = []
    
    if start_date:
        where_clauses.append("DATE(work_date) >= DATE(?)")
        parameters.append(start_date)
    
    if end_date:
        where_clauses.append("DATE(work_date) <= DATE(?)")
        parameters.append(end_date)

    if technician:
        where_clauses.append("technician = ?")
        parameters.append(technician)
    
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    with get_connection() as connection:
        # Get total by technician
        tech_rows = connection.execute(
            f"""
            SELECT technician, SUM(hours_worked) AS total_hours
            FROM technician_hours
            WHERE {where_clause}
            GROUP BY technician
            ORDER BY total_hours DESC
            """,
            parameters,
        ).fetchall()
        
        by_technician = {row["technician"]: round(row["total_hours"], 2) for row in tech_rows}
        
        # Get overall total
        total_row = connection.execute(
            f"""
            SELECT SUM(hours_worked) AS total_hours
            FROM technician_hours
            WHERE {where_clause}
            """,
            parameters,
        ).fetchone()
        
        total_hours = round(total_row["total_hours"] or 0, 2)
    
    return {
        "by_technician": by_technician,
        "total_hours": total_hours,
        "date_range": {
            "start": start_date or "all",
            "end": end_date or "all",
        },
    }


def create_inventory_purchase(payload: dict) -> dict:
    timestamp = utc_now()
    purchase_date = payload.get("purchase_date") or timestamp[:10]
    line_items = payload.get("items", [])
    total_cost = float(payload.get("total_cost", 0) or 0)

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO inventory_purchases (
                purchase_date,
                vendor,
                reference_number,
                total_cost,
                notes,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                purchase_date,
                payload.get("vendor"),
                payload.get("reference_number"),
                total_cost,
                payload.get("notes"),
                timestamp,
                timestamp,
            ),
        )
        purchase_id = int(cursor.lastrowid)
        for item in line_items:
            quantity = int(item.get("quantity", 0))
            unit_cost = item.get("estimated_unit_cost")
            line_total = item.get("line_total")
            if line_total is None and unit_cost is not None:
                line_total = float(unit_cost) * quantity
            connection.execute(
                """
                INSERT INTO inventory_purchase_items (
                    purchase_id,
                    item_type,
                    manufacturer,
                    item_name,
                    quantity,
                    estimated_unit_cost,
                    line_total,
                    notes,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    purchase_id,
                    item.get("item_type", "device"),
                    item.get("manufacturer"),
                    item["item_name"],
                    quantity,
                    unit_cost,
                    line_total,
                    item.get("notes"),
                    timestamp,
                    timestamp,
                ),
            )
        connection.commit()

    return get_inventory_purchase(purchase_id)


def _list_inventory_purchase_items(connection: sqlite3.Connection, purchase_id: int) -> list[dict]:
    rows = connection.execute(
        """
        SELECT id, purchase_id, item_type, manufacturer, item_name, quantity,
               estimated_unit_cost, line_total, notes, created_at, updated_at
        FROM inventory_purchase_items
        WHERE purchase_id = ?
        ORDER BY id ASC
        """,
        (purchase_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def list_inventory_purchases() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, purchase_date, vendor, reference_number, total_cost, notes, created_at, updated_at
            FROM inventory_purchases
            ORDER BY purchase_date DESC, id DESC
            """
        ).fetchall()
        purchases = []
        for row in rows:
            item = dict(row)
            item["items"] = _list_inventory_purchase_items(connection, item["id"])
            purchases.append(item)
    return purchases


def get_inventory_purchase(purchase_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, purchase_date, vendor, reference_number, total_cost, notes, created_at, updated_at
            FROM inventory_purchases
            WHERE id = ?
            """,
            (purchase_id,),
        ).fetchone()
        if row is None:
            return None
        item = dict(row)
        item["items"] = _list_inventory_purchase_items(connection, purchase_id)
    return item


def get_report_summary(
    start_date: str | None = None,
    end_date: str | None = None,
    technician: str | None = None,
    repair_category: str | None = None,
) -> dict:
    """Aggregate high-level business reporting metrics for a date range."""
    def build_ticket_filters(date_field: str, include_closed_only: bool = False) -> tuple[str, list]:
        where_clauses: list[str] = []
        parameters: list = []

        if include_closed_only:
            where_clauses.append("repair_tickets.status = 'Picked Up / Closed'")

        if start_date:
            where_clauses.append(f"date({date_field}) >= date(?)")
            parameters.append(start_date)

        if end_date:
            where_clauses.append(f"date({date_field}) <= date(?)")
            parameters.append(end_date)

        if technician:
            where_clauses.append(
                """
                (
                    repair_tickets.assigned_technician = ?
                    OR EXISTS (
                        SELECT 1
                        FROM technician_hours
                        WHERE technician_hours.ticket_id = repair_tickets.id
                          AND technician_hours.technician = ?
                    )
                )
                """
            )
            parameters.extend([technician, technician])

        if repair_category:
            where_clauses.append(
                """
                EXISTS (
                    SELECT 1
                    FROM repair_actions
                    JOIN repair_categories ON repair_categories.id = repair_actions.repair_category_id
                    WHERE repair_actions.ticket_id = repair_tickets.id
                      AND repair_categories.name = ?
                )
                """
            )
            parameters.append(repair_category)

        return (" AND ".join(where_clauses) if where_clauses else "1=1", parameters)

    def build_hours_filters() -> tuple[str, list]:
        where_clauses: list[str] = []
        parameters: list = []

        if start_date:
            where_clauses.append("date(technician_hours.work_date) >= date(?)")
            parameters.append(start_date)

        if end_date:
            where_clauses.append("date(technician_hours.work_date) <= date(?)")
            parameters.append(end_date)

        if technician:
            where_clauses.append("technician_hours.technician = ?")
            parameters.append(technician)

        if repair_category:
            where_clauses.append(
                """
                EXISTS (
                    SELECT 1
                    FROM repair_actions
                    JOIN repair_categories ON repair_categories.id = repair_actions.repair_category_id
                    WHERE repair_actions.ticket_id = technician_hours.ticket_id
                      AND repair_categories.name = ?
                )
                """
            )
            parameters.append(repair_category)

        return (" AND ".join(where_clauses) if where_clauses else "1=1", parameters)

    created_where_clause, created_parameters = build_ticket_filters("repair_tickets.intake_date")
    closed_where_clause, closed_parameters = build_ticket_filters("repair_tickets.updated_at", include_closed_only=True)
    hours_where_clause, hours_parameters = build_hours_filters()

    with get_connection() as connection:
        created_row = connection.execute(
            f"""
            SELECT COUNT(*) AS created_tickets_count
            FROM repair_tickets
            WHERE {created_where_clause}
            """,
            created_parameters,
        ).fetchone()

        closed_row = connection.execute(
            f"""
            SELECT
                COUNT(*) AS closed_tickets_count,
                SUM(final_price) AS total_revenue
            FROM repair_tickets
            WHERE {closed_where_clause}
            """,
            closed_parameters,
        ).fetchone()

        total_hours_row = connection.execute(
            f"""
            SELECT SUM(technician_hours.hours_worked) AS total_hours
            FROM technician_hours
            WHERE {hours_where_clause}
            """,
            hours_parameters,
        ).fetchone()

        technician_rows = connection.execute(
            f"""
            SELECT
                technician_hours.technician,
                ROUND(SUM(technician_hours.hours_worked), 2) AS total_hours,
                COUNT(DISTINCT technician_hours.ticket_id) AS tickets_worked
            FROM technician_hours
            WHERE {hours_where_clause}
            GROUP BY technician_hours.technician
            ORDER BY total_hours DESC, technician_hours.technician ASC
            """,
            hours_parameters,
        ).fetchall()

        repair_category_where_clauses = []
        repair_category_parameters: list = []
        if start_date:
            repair_category_where_clauses.append("date(repair_tickets.updated_at) >= date(?)")
            repair_category_parameters.append(start_date)
        if end_date:
            repair_category_where_clauses.append("date(repair_tickets.updated_at) <= date(?)")
            repair_category_parameters.append(end_date)
        if technician:
            repair_category_where_clauses.append(
                """
                (
                    repair_tickets.assigned_technician = ?
                    OR EXISTS (
                        SELECT 1
                        FROM technician_hours
                        WHERE technician_hours.ticket_id = repair_tickets.id
                          AND technician_hours.technician = ?
                    )
                )
                """
            )
            repair_category_parameters.extend([technician, technician])
        if repair_category:
            repair_category_where_clauses.append("repair_categories.name = ?")
            repair_category_parameters.append(repair_category)

        repair_category_where_clause = " AND ".join(repair_category_where_clauses) if repair_category_where_clauses else "1=1"

        category_rows = connection.execute(
            f"""
            SELECT
                repair_categories.name AS repair_category,
                COUNT(repair_actions.id) AS action_count,
                COUNT(DISTINCT repair_actions.ticket_id) AS ticket_count,
                ROUND(SUM(COALESCE(repair_actions.final_price, repair_actions.calculated_price, 0)), 2) AS total_final_price
            FROM repair_actions
            JOIN repair_categories ON repair_categories.id = repair_actions.repair_category_id
            JOIN repair_tickets ON repair_tickets.id = repair_actions.ticket_id
            WHERE {repair_category_where_clause}
            GROUP BY repair_categories.name
            ORDER BY total_final_price DESC, repair_categories.name ASC
            """,
            repair_category_parameters,
        ).fetchall()

        technician_options = connection.execute(
            """
            SELECT technician FROM technician_hours
            WHERE technician IS NOT NULL AND TRIM(technician) != ''
            UNION
            SELECT assigned_technician AS technician FROM repair_tickets
            WHERE assigned_technician IS NOT NULL AND TRIM(assigned_technician) != ''
            ORDER BY technician ASC
            """
        ).fetchall()

        repair_category_options = connection.execute(
            """
            SELECT name
            FROM repair_categories
            WHERE active = 1
            ORDER BY name ASC
            """
        ).fetchall()

        technician_breakdown = []
        for row in technician_rows:
            technician_name = row["technician"]
            filtered_closed_where, filtered_closed_parameters = build_ticket_filters(
                "repair_tickets.updated_at",
                include_closed_only=True,
            )
            filtered_closed_where = f"{filtered_closed_where} AND (repair_tickets.assigned_technician = ? OR EXISTS (SELECT 1 FROM technician_hours WHERE technician_hours.ticket_id = repair_tickets.id AND technician_hours.technician = ?))"
            filtered_closed_parameters = [*filtered_closed_parameters, technician_name, technician_name]
            technician_closed_row = connection.execute(
                f"""
                SELECT
                    COUNT(*) AS closed_tickets_count,
                    ROUND(SUM(repair_tickets.final_price), 2) AS total_revenue
                FROM repair_tickets
                WHERE {filtered_closed_where}
                """,
                filtered_closed_parameters,
            ).fetchone()
            technician_breakdown.append(
                {
                    "technician": technician_name,
                    "total_hours": row["total_hours"] or 0,
                    "tickets_worked": row["tickets_worked"] or 0,
                    "closed_tickets_count": technician_closed_row["closed_tickets_count"] or 0,
                    "total_revenue": round(technician_closed_row["total_revenue"] or 0, 2),
                }
            )

    total_hours = round(total_hours_row["total_hours"] or 0, 2)
    closed_tickets_count = closed_row["closed_tickets_count"] or 0
    total_revenue = round(closed_row["total_revenue"] or 0, 2)
    average_closed_ticket_revenue = round(total_revenue / closed_tickets_count, 2) if closed_tickets_count else 0
    revenue_per_hour = round(total_revenue / total_hours, 2) if total_hours else 0

    return {
        "date_range": {
            "start": start_date or "all",
            "end": end_date or "all",
        },
        "technician_filter": technician,
        "repair_category_filter": repair_category,
        "created_tickets_count": created_row["created_tickets_count"] or 0,
        "closed_tickets_count": closed_tickets_count,
        "total_revenue": total_revenue,
        "average_closed_ticket_revenue": average_closed_ticket_revenue,
        "total_hours": total_hours,
        "revenue_per_hour": revenue_per_hour,
        "available_technicians": [row["technician"] for row in technician_options],
        "available_repair_categories": [row["name"] for row in repair_category_options],
        "technician_breakdown": technician_breakdown,
        "repair_category_breakdown": [
            {
                "repair_category": row["repair_category"],
                "action_count": row["action_count"] or 0,
                "ticket_count": row["ticket_count"] or 0,
                "total_final_price": round(row["total_final_price"] or 0, 2),
            }
            for row in category_rows
        ],
    }


# ============================================================================
# Phase 5: Inventory and Donor Devices
# ============================================================================


PART_STATUSES = {
    "In Stock",
    "Low Stock",
    "Ordered",
    "Backordered",
    "Discontinued",
    "Donor Only",
}

DONOR_STATUSES = {
    "Available for Parts",
    "Partially Harvested",
    "Fully Harvested",
    "Repairable Resale",
    "Retired/Discarded",
}

INVENTORY_MOVEMENT_TYPES = {
    "add",
    "consume",
    "adjust",
    "transfer",
    "donor_harvest",
    "return",
    "correction",
}


def _normalize_part(row: sqlite3.Row | None) -> dict | None:
    data = row_to_dict(row)
    return data


def _normalize_donor(row: sqlite3.Row | None) -> dict | None:
    data = row_to_dict(row)
    if data is None:
        return None
    data["parts_harvested"] = json.loads(data["parts_harvested"] or "[]")
    data["parts_available"] = json.loads(data["parts_available"] or "[]")
    return data


def list_parts(category: str | None = None, status: str | None = None, low_stock_only: bool = False) -> list[dict]:
    where_clauses = ["1=1"]
    parameters: list = []
    if category:
        where_clauses.append("category = ?")
        parameters.append(category)
    if status:
        where_clauses.append("status = ?")
        parameters.append(status)
    if low_stock_only:
        where_clauses.append("quantity_on_hand <= reorder_level")
    where_sql = " AND ".join(where_clauses)

    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT id, part_number, part_name, device_compatibility, category,
                   supplier, cost, retail_price, status, quantity_on_hand,
                   quantity_ordered, reorder_level, reorder_quantity, notes,
                   created_at, updated_at
            FROM parts
            WHERE {where_sql}
            ORDER BY part_name ASC, id ASC
            """,
            parameters,
        ).fetchall()
    return [dict(row) for row in rows]


def get_part(part_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, part_number, part_name, device_compatibility, category,
                   supplier, cost, retail_price, status, quantity_on_hand,
                   quantity_ordered, reorder_level, reorder_quantity, notes,
                   created_at, updated_at
            FROM parts
            WHERE id = ?
            """,
            (part_id,),
        ).fetchone()
    return _normalize_part(row)


def create_part(payload: dict) -> dict:
    status = payload.get("status", "In Stock")
    if status not in PART_STATUSES:
        raise ValueError("Invalid part status")
    timestamp = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO parts (
                part_number, part_name, device_compatibility, category, supplier,
                cost, retail_price, status, quantity_on_hand, quantity_ordered,
                reorder_level, reorder_quantity, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["part_number"],
                payload["part_name"],
                payload.get("device_compatibility"),
                payload["category"],
                payload.get("supplier"),
                payload.get("cost"),
                payload.get("retail_price"),
                status,
                int(payload.get("quantity_on_hand", 0)),
                int(payload.get("quantity_ordered", 0)),
                int(payload.get("reorder_level", 5)),
                int(payload.get("reorder_quantity", 10)),
                payload.get("notes"),
                timestamp,
                timestamp,
            ),
        )
        connection.commit()
    part = get_part(cursor.lastrowid)
    if part is None:
        raise ValueError("Failed to create part")
    return part


def update_part(part_id: int, payload: dict) -> dict | None:
    existing = get_part(part_id)
    if existing is None:
        return None
    if "status" in payload and payload["status"] not in PART_STATUSES:
        raise ValueError("Invalid part status")

    allowed_fields = {
        "part_number",
        "part_name",
        "device_compatibility",
        "category",
        "supplier",
        "cost",
        "retail_price",
        "status",
        "quantity_on_hand",
        "quantity_ordered",
        "reorder_level",
        "reorder_quantity",
        "notes",
    }
    updates = {k: v for k, v in payload.items() if k in allowed_fields}
    if not updates:
        return existing

    set_parts = []
    parameters: list = []
    for key, value in updates.items():
        set_parts.append(f"{key} = ?")
        parameters.append(value)
    set_parts.append("updated_at = ?")
    parameters.append(utc_now())
    parameters.append(part_id)

    with get_connection() as connection:
        connection.execute(
            f"UPDATE parts SET {', '.join(set_parts)} WHERE id = ?",
            parameters,
        )
        connection.commit()
    return get_part(part_id)


def delete_part(part_id: int) -> bool:
    updated = update_part(part_id, {"status": "Discontinued"})
    return updated is not None


def list_donors(status: str | None = None, device_model: str | None = None) -> list[dict]:
    where_clauses = ["1=1"]
    parameters: list = []
    if status:
        where_clauses.append("status = ?")
        parameters.append(status)
    if device_model:
        where_clauses.append("device_model = ?")
        parameters.append(device_model)
    where_sql = " AND ".join(where_clauses)

    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT id, device_identifier, device_model, status,
                   condition_notes, parts_harvested, parts_available,
                   acquisition_date, retirement_date, created_at, updated_at
            FROM donor_devices
            WHERE {where_sql}
            ORDER BY created_at DESC, id DESC
            """,
            parameters,
        ).fetchall()
    return [_normalize_donor(row) for row in rows if row is not None]


def get_donor(donor_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, device_identifier, device_model, status,
                   condition_notes, parts_harvested, parts_available,
                   acquisition_date, retirement_date, created_at, updated_at
            FROM donor_devices
            WHERE id = ?
            """,
            (donor_id,),
        ).fetchone()
    return _normalize_donor(row)


def create_donor(payload: dict) -> dict:
    status = payload.get("status", "Available for Parts")
    if status not in DONOR_STATUSES:
        raise ValueError("Invalid donor status")
    timestamp = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO donor_devices (
                device_identifier, device_model, status, condition_notes,
                parts_harvested, parts_available, acquisition_date,
                retirement_date, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["device_identifier"],
                payload["device_model"],
                status,
                payload.get("condition_notes"),
                json.dumps(payload.get("parts_harvested", [])),
                json.dumps(payload.get("parts_available", [])),
                payload.get("acquisition_date"),
                payload.get("retirement_date"),
                timestamp,
                timestamp,
            ),
        )
        connection.commit()
    donor = get_donor(cursor.lastrowid)
    if donor is None:
        raise ValueError("Failed to create donor")
    return donor


def update_donor(donor_id: int, payload: dict) -> dict | None:
    existing = get_donor(donor_id)
    if existing is None:
        return None
    if "status" in payload and payload["status"] not in DONOR_STATUSES:
        raise ValueError("Invalid donor status")

    allowed_fields = {
        "device_identifier",
        "device_model",
        "status",
        "condition_notes",
        "parts_harvested",
        "parts_available",
        "acquisition_date",
        "retirement_date",
    }
    updates = {k: v for k, v in payload.items() if k in allowed_fields}
    if not updates:
        return existing

    set_parts = []
    parameters: list = []
    for key, value in updates.items():
        if key in {"parts_harvested", "parts_available"}:
            set_parts.append(f"{key} = ?")
            parameters.append(json.dumps(value))
        else:
            set_parts.append(f"{key} = ?")
            parameters.append(value)

    set_parts.append("updated_at = ?")
    parameters.append(utc_now())
    parameters.append(donor_id)

    with get_connection() as connection:
        connection.execute(
            f"UPDATE donor_devices SET {', '.join(set_parts)} WHERE id = ?",
            parameters,
        )
        connection.commit()
    return get_donor(donor_id)


def harvest_part_from_donor(donor_id: int, part_id: int) -> dict | None:
    donor = get_donor(donor_id)
    if donor is None:
        return None
    if get_part(part_id) is None:
        raise ValueError("Part not found")

    harvested = set(int(value) for value in donor.get("parts_harvested", []))
    available = set(int(value) for value in donor.get("parts_available", []))
    if part_id in harvested:
        raise ValueError("Part already harvested from donor")
    if part_id in available:
        available.remove(part_id)
    harvested.add(part_id)

    status = donor["status"]
    if status == "Available for Parts":
        status = "Partially Harvested"

    return update_donor(
        donor_id,
        {
            "status": status,
            "parts_harvested": sorted(harvested),
            "parts_available": sorted(available),
        },
    )


def log_part_usage(repair_action_id: int, part_id: int, quantity_used: int = 1) -> dict:
    if quantity_used <= 0:
        raise ValueError("Quantity must be greater than zero")

    with get_connection() as connection:
        repair_action = connection.execute(
            "SELECT id FROM repair_actions WHERE id = ?",
            (repair_action_id,),
        ).fetchone()
        if repair_action is None:
            raise ValueError("Repair action not found")

        part_row = connection.execute(
            "SELECT id, quantity_on_hand, status FROM parts WHERE id = ?",
            (part_id,),
        ).fetchone()
        if part_row is None:
            raise ValueError("Part not found")
        if part_row["status"] == "Backordered":
            raise ValueError("Backordered parts cannot be used")
        if part_row["quantity_on_hand"] < quantity_used:
            raise ValueError("Insufficient stock for part usage")

        timestamp = utc_now()
        cursor = connection.execute(
            """
            INSERT INTO part_usage (repair_action_id, part_id, quantity_used, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (repair_action_id, part_id, quantity_used, timestamp),
        )
        connection.execute(
            """
            UPDATE parts
            SET quantity_on_hand = quantity_on_hand - ?,
                updated_at = ?
            WHERE id = ?
            """,
            (quantity_used, timestamp, part_id),
        )
        connection.commit()

    usage = get_part_usage_entry(cursor.lastrowid)
    if usage is None:
        raise ValueError("Failed to create part usage entry")
    return usage


def get_part_usage_entry(usage_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT pu.id, pu.repair_action_id, pu.part_id, pu.quantity_used, pu.created_at,
                   p.part_number, p.part_name, p.category
            FROM part_usage pu
            JOIN parts p ON p.id = pu.part_id
            WHERE pu.id = ?
            """,
            (usage_id,),
        ).fetchone()
    return row_to_dict(row)


def get_part_usage_for_repair_action(repair_action_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT pu.id, pu.repair_action_id, pu.part_id, pu.quantity_used, pu.created_at,
                   p.part_number, p.part_name, p.category
            FROM part_usage pu
            JOIN parts p ON p.id = pu.part_id
            WHERE pu.repair_action_id = ?
            ORDER BY pu.created_at DESC, pu.id DESC
            """,
            (repair_action_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_part_usage_history(part_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT pu.id, pu.repair_action_id, pu.part_id, pu.quantity_used, pu.created_at,
                   ra.ticket_id, p.part_number, p.part_name, p.category
            FROM part_usage pu
            JOIN parts p ON p.id = pu.part_id
            JOIN repair_actions ra ON ra.id = pu.repair_action_id
            WHERE pu.part_id = ?
            ORDER BY pu.created_at DESC, pu.id DESC
            """,
            (part_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_low_stock_parts() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, part_number, part_name, device_compatibility, category,
                   supplier, cost, retail_price, status, quantity_on_hand,
                   quantity_ordered, reorder_level, reorder_quantity, notes,
                   created_at, updated_at
            FROM parts
            WHERE quantity_on_hand <= reorder_level
              AND status NOT IN ('Discontinued')
            ORDER BY quantity_on_hand ASC, part_name ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def create_inventory_movement(
    *,
    movement_type: str,
    quantity: int,
    part_id: int | None = None,
    donor_id: int | None = None,
    reason: str | None = None,
    ticket_id: int | None = None,
    repair_action_id: int | None = None,
    actor_user_id: int | None = None,
    request_id: str | None = None,
    metadata: dict | None = None,
) -> dict:
    if movement_type not in INVENTORY_MOVEMENT_TYPES:
        raise ValueError("Invalid inventory movement type")

    if quantity == 0:
        raise ValueError("Movement quantity cannot be zero")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO inventory_movements (
                part_id,
                donor_id,
                movement_type,
                quantity,
                reason,
                ticket_id,
                repair_action_id,
                actor_user_id,
                request_id,
                metadata_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                part_id,
                donor_id,
                movement_type,
                quantity,
                reason,
                ticket_id,
                repair_action_id,
                actor_user_id,
                request_id,
                json.dumps(metadata) if metadata is not None else None,
                utc_now(),
            ),
        )
        movement_id = cursor.lastrowid
        connection.commit()

        row = connection.execute(
            "SELECT * FROM inventory_movements WHERE id = ?",
            (movement_id,),
        ).fetchone()

    item = row_to_dict(row)
    if item is None:
        raise ValueError("Failed to create inventory movement")
    item["metadata"] = json.loads(item["metadata_json"]) if item.get("metadata_json") else None
    item.pop("metadata_json", None)
    return item


def list_inventory_movements(
    *,
    page: int = 1,
    page_size: int = 50,
    part_id: int | None = None,
    movement_type: str | None = None,
) -> dict:
    page = max(1, page)
    page_size = max(1, min(500, page_size))
    where_clauses = ["1=1"]
    params: list = []
    if part_id is not None:
        where_clauses.append("part_id = ?")
        params.append(part_id)
    if movement_type is not None:
        where_clauses.append("movement_type = ?")
        params.append(movement_type)

    where_sql = " AND ".join(where_clauses)
    offset = (page - 1) * page_size

    with get_connection() as connection:
        total_row = connection.execute(
            f"SELECT COUNT(*) AS count FROM inventory_movements WHERE {where_sql}",
            tuple(params),
        ).fetchone()

        rows = connection.execute(
            f"""
            SELECT * FROM inventory_movements
            WHERE {where_sql}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            tuple(params + [page_size, offset]),
        ).fetchall()

    items = []
    for row in rows:
        item = dict(row)
        item["metadata"] = json.loads(item["metadata_json"]) if item.get("metadata_json") else None
        item.pop("metadata_json", None)
        items.append(item)

    total = int(total_row["count"]) if total_row else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def create_inventory_reconciliation(
    *,
    part_id: int,
    expected_quantity: int,
    actual_quantity: int,
    reason: str,
    resolved_by: str | None,
) -> dict:
    discrepancy = actual_quantity - expected_quantity
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO inventory_reconciliations (
                part_id,
                expected_quantity,
                actual_quantity,
                discrepancy,
                reason,
                resolved_by,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                part_id,
                expected_quantity,
                actual_quantity,
                discrepancy,
                reason,
                resolved_by,
                utc_now(),
            ),
        )
        reconciliation_id = cursor.lastrowid
        connection.commit()

        row = connection.execute(
            "SELECT * FROM inventory_reconciliations WHERE id = ?",
            (reconciliation_id,),
        ).fetchone()

    item = row_to_dict(row)
    if item is None:
        raise ValueError("Failed to create reconciliation record")
    return item


def list_inventory_reconciliations(part_id: int | None = None) -> list[dict]:
    where_sql = "WHERE part_id = ?" if part_id is not None else ""
    params = (part_id,) if part_id is not None else ()
    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT * FROM inventory_reconciliations
            {where_sql}
            ORDER BY id DESC
            """,
            params,
        ).fetchall()
    return [dict(row) for row in rows]


def create_attachment_metadata(
    *,
    attachment_type: str,
    entity_type: str,
    entity_id: int,
    storage_key: str,
    original_filename: str,
    mime_type: str,
    file_size: int,
    uploaded_by: int | None,
) -> dict:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO attachments (
                attachment_type,
                entity_type,
                entity_id,
                storage_key,
                original_filename,
                mime_type,
                file_size,
                uploaded_by,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attachment_type,
                entity_type,
                entity_id,
                storage_key,
                original_filename,
                mime_type,
                file_size,
                uploaded_by,
                utc_now(),
            ),
        )
        attachment_id = cursor.lastrowid
        connection.commit()

        row = connection.execute(
            "SELECT * FROM attachments WHERE id = ?",
            (attachment_id,),
        ).fetchone()

    item = row_to_dict(row)
    if item is None:
        raise ValueError("Failed to create attachment metadata")
    return item


def get_attachment_metadata(attachment_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM attachments WHERE id = ?",
            (attachment_id,),
        ).fetchone()
    return row_to_dict(row)


def list_attachments_for_entity(entity_type: str, entity_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM attachments
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY id DESC
            """,
            (entity_type, entity_id),
        ).fetchall()
    return [dict(row) for row in rows]


def delete_attachment_metadata(attachment_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM attachments WHERE id = ?",
            (attachment_id,),
        ).fetchone()
        if row is None:
            return None

        connection.execute(
            "DELETE FROM attachments WHERE id = ?",
            (attachment_id,),
        )
        connection.commit()
    return dict(row)


def list_attachment_storage_keys() -> list[str]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT storage_key FROM attachments",
        ).fetchall()
    return [str(row["storage_key"]) for row in rows]

