from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

import app.database as database


HOURLY_RATE = 20.0
PERSISTENT_SQLITE_PREFIXES = ("/var/data/",)
TICKET_ENTITY_TYPES = {
    "repair_ticket",
    "repair_tickets",
    "ticket",
    "tickets",
}
REPAIR_ACTION_ENTITY_TYPES = {
    "repair_action",
    "repair_actions",
}
ACTIVITY_LOG_ENTITY_TYPES = {
    "repair_ticket",
    "repair_tickets",
    "ticket",
    "tickets",
    "repair_action",
    "repair_actions",
    "loaner_checkout",
    "loaner_checkouts",
    "hours",
    "technician_hours",
    "clock_session",
    "technician_clock_sessions",
    "part_usage",
    "inventory_movement",
}

REAL_CUSTOMERS = [
    {
        "full_name": "Yossi Weiss",
        "phone": None,
        "notes": "First Tech Restore customer repair. Wonder phone touchpad replacement. Customer supplied the part.",
    },
    {
        "full_name": "Yossi Toder",
        "phone": "732-664-1835",
        "notes": "Alcatel 4044T SIM card reader evaluation. Customer declined complicated or expensive repair.",
    },
    {
        "full_name": "Ungar",
        "phone": "732-363-3950",
        "notes": "Kyocera E4810 white-screen repair completed on the house because TAG sold the phone.",
    },
    {
        "full_name": "Unknown Screen Customer",
        "phone": "732-237-4070",
        "notes": "Samsung Galaxy A13 5G / SM-A136U1 screen estimate. Customer declined the repair.",
    },
]


REAL_TICKETS = [
    {
        "ticket_number": "TR-REAL-20260507-01",
        "customer_name": "Yossi Weiss",
        "phone": None,
        "device": "Wonder phone",
        "issue_category": "Touchpad replacement",
        "issue_description": "Touchpad replacement on Wonder phone using a customer-supplied part.",
        "condition_summary": "Customer supplied the part. About 20 minutes of bench time.",
        "estimated_price": 35.0,
        "final_price": 25.0,
        "payment_status": "unpaid",
        "status": "Picked Up / Closed",
        "intake_date": "2026-05-07T09:00:00+00:00",
        "created_at": "2026-05-07T09:00:00+00:00",
        "updated_at": "2026-05-07T09:20:00+00:00",
        "status_history": [
            (None, "New Intake", "Mattis", "Real Tech Restore import: initial intake.", "2026-05-07T09:00:00+00:00"),
            ("New Intake", "Picked Up / Closed", "Mattis", "Touchpad replacement completed. Customer still owes $25.", "2026-05-07T09:20:00+00:00"),
        ],
        "notes": [
            ("front_desk", "First Tech Restore customer repair. Customer supplied the part for a Wonder phone touchpad replacement.", "Mattis", "2026-05-07T09:02:00+00:00"),
            ("pricing", "Standard price would be $35. Actual charge is $25. Payment remains unpaid and the customer still owes $25.", "Mattis", "2026-05-07T09:05:00+00:00"),
            ("parts", "Customer supplied the replacement part.", "Mattis", "2026-05-07T09:06:00+00:00"),
            ("technician", "Completed in about 20 minutes and verified touch response before release.", "Mattis", "2026-05-07T09:18:00+00:00"),
        ],
    },
    {
        "ticket_number": "TR-REAL-20260513-01",
        "customer_name": "Yossi Toder",
        "phone": "732-664-1835",
        "device": "Alcatel 4044T",
        "issue_category": "SIM card not reading",
        "issue_description": "Phone would not read a SIM card. SIM reader looked very damaged.",
        "condition_summary": "Customer did not want the repair if it was complicated or expensive.",
        "estimated_price": 0.0,
        "final_price": 0.0,
        "payment_status": "paid",
        "status": "Customer Declined",
        "intake_date": "2026-05-13T10:00:00+00:00",
        "created_at": "2026-05-13T10:00:00+00:00",
        "updated_at": "2026-05-13T10:30:00+00:00",
        "status_history": [
            (None, "New Intake", "Mattis", "Real Tech Restore import: initial intake.", "2026-05-13T10:00:00+00:00"),
            ("New Intake", "Needs Diagnosis", "Mattis", "SIM reader looked very damaged.", "2026-05-13T10:12:00+00:00"),
            ("Needs Diagnosis", "Customer Declined", "Mattis", "Adjusted SIM reader slightly and tested with a SIM card. Device still did not read the SIM card. Customer declined a complicated or expensive repair.", "2026-05-13T10:30:00+00:00"),
        ],
        "notes": [
            ("front_desk", "Customer said they only wanted the repair if it was simple and inexpensive.", "Mattis", "2026-05-13T10:03:00+00:00"),
            ("technician", "Adjusted the SIM reader slightly and tested with a SIM card. The phone still did not read the SIM card.", "Mattis", "2026-05-13T10:20:00+00:00"),
            ("pricing", "No diagnosis charge. Final charge is $0 because the customer declined the repair.", "Mattis", "2026-05-13T10:24:00+00:00"),
            ("internal", "Customer was told the phone could not be fixed economically and it was not worth doing.", "Mattis", "2026-05-13T10:26:00+00:00"),
        ],
    },
    {
        "ticket_number": "TR-REAL-20260602-01",
        "customer_name": "Ungar",
        "phone": "732-363-3950",
        "device": "Kyocera E4810",
        "issue_category": "White screen",
        "issue_description": "Kyocera E4810 showed a white screen. Diagnosis confirmed the issue was the display assembly.",
        "condition_summary": "Completed on the house because TAG sold the phone.",
        "estimated_price": 85.0,
        "final_price": 0.0,
        "payment_status": "paid",
        "status": "Picked Up / Closed",
        "intake_date": "2026-06-02T11:00:00+00:00",
        "created_at": "2026-06-02T11:00:00+00:00",
        "updated_at": "2026-06-02T12:30:00+00:00",
        "status_history": [
            (None, "New Intake", "Mattis", "Real Tech Restore import: initial intake.", "2026-06-02T11:00:00+00:00"),
            ("New Intake", "Needs Diagnosis", "Mattis", "White-screen issue confirmed during diagnosis.", "2026-06-02T11:20:00+00:00"),
            ("Needs Diagnosis", "Picked Up / Closed", "Mattis", "Screen replacement completed. Standard screen-only price is $85, but this repair was done on the house because TAG sold the phone.", "2026-06-02T12:30:00+00:00"),
        ],
        "notes": [
            ("front_desk", "Customer phone came in with a white screen on a Kyocera E4810.", "Mattis", "2026-06-02T11:02:00+00:00"),
            ("pricing", "E4810 white-screen pricing rule: if it is only a screen issue, charge $85. If it is a cable or shell issue, do an MBS/shell swap and charge $120. No diagnosis charge.", "Mattis", "2026-06-02T11:25:00+00:00"),
            ("internal", "Customer-facing wording: 'I don't charge to check it. If it only needs the screen replaced, it's $85. If it needs the full shell/board swap, it's $120. I'll check it first and let you know which one it is.' User does not do cable swaps; for cable/shell issues, user does an MBS/shell swap instead.", "Mattis", "2026-06-02T11:26:00+00:00"),
            ("parts", "Standard E4810 white-screen shell/MBS cost basis is about $60 if a donor shell swap is needed.", "Mattis", "2026-06-02T11:27:00+00:00"),
            ("technician", "Diagnosis confirmed it was just the screen. Replaced the screen and closed the ticket on the house.", "Mattis", "2026-06-02T12:20:00+00:00"),
        ],
    },
    {
        "ticket_number": "TR-REAL-20260525-01",
        "customer_name": "Unknown Screen Customer",
        "phone": "732-237-4070",
        "device": "Samsung Galaxy A13 5G / SM-A136U1",
        "issue_category": "Screen repair estimate",
        "issue_description": "Customer needed the correct Samsung Galaxy A13 5G screen with frame. The correct model was identified as SM-A136U1.",
        "condition_summary": "Customer ended up not wanting the repair.",
        "estimated_price": 0.0,
        "final_price": 0.0,
        "payment_status": "paid",
        "status": "Customer Declined",
        "intake_date": "2026-05-25T15:00:00+00:00",
        "created_at": "2026-05-25T15:00:00+00:00",
        "updated_at": "2026-05-25T15:40:00+00:00",
        "status_history": [
            (None, "New Intake", "Mattis", "Real Tech Restore import: initial intake.", "2026-05-25T15:00:00+00:00"),
            ("New Intake", "Customer Declined", "Mattis", "Correct model identified as Samsung Galaxy A13 5G / SM-A136U1. Customer decided not to move forward with the screen repair.", "2026-05-25T15:40:00+00:00"),
        ],
        "notes": [
            ("front_desk", "This was a screen repair request. It was not a Waze setup job.", "Mattis", "2026-05-25T15:03:00+00:00"),
            ("technician", "Identified the correct model as Samsung Galaxy A13 5G / SM-A136U1 and confirmed the job needed the correct screen with frame.", "Mattis", "2026-05-25T15:15:00+00:00"),
            ("pricing", "No charge because the customer declined the repair before any paid work was authorized.", "Mattis", "2026-05-25T15:20:00+00:00"),
            ("internal", "Customer ended up not wanting to do the screen repair after the correct model identification work.", "Mattis", "2026-05-25T15:25:00+00:00"),
        ],
    },
]


REAL_HOURS = [
    {"work_date": "2026-05-07", "hours_worked": 1.5, "work_description": "Wonder phone touchpad replacement for Yossi Weiss.", "ticket_number": "TR-REAL-20260507-01"},
    {"work_date": "2026-05-10", "hours_worked": 3.3333333333, "work_description": "General Tech Restore bench work and repair prep.", "ticket_number": None},
    {"work_date": "2026-05-13", "hours_worked": 0.5, "work_description": "Alcatel 4044T SIM reader diagnosis for Yossi Toder.", "ticket_number": "TR-REAL-20260513-01"},
    {"work_date": "2026-05-14", "hours_worked": 0.5, "work_description": "Bench cleanup, follow-up, and repair organization.", "ticket_number": None},
    {"work_date": "2026-05-24", "hours_worked": 1.0, "work_description": "General repair shop work.", "ticket_number": None},
    {"work_date": "2026-05-25", "hours_worked": 1.1666666667, "work_description": "Samsung Galaxy A13 5G / SM-A136U1 model identification and screen estimate.", "ticket_number": "TR-REAL-20260525-01"},
    {"work_date": "2026-05-26", "hours_worked": 2.0, "work_description": "Kyocera E4810 white-screen diagnosis and repair prep.", "ticket_number": "TR-REAL-20260602-01"},
    {"work_date": "2026-05-27", "hours_worked": 1.3333333333, "work_description": "Kyocera E4810 screen replacement bench work.", "ticket_number": "TR-REAL-20260602-01"},
    {"work_date": "2026-06-01", "hours_worked": 1.6666666667, "work_description": "Yesterday entry: Tech Restore queue follow-up and shop work.", "ticket_number": None},
    {"work_date": "2026-06-02", "hours_worked": 1.0, "work_description": "Today entry: final closeout and delivery work.", "ticket_number": "TR-REAL-20260602-01"},
]


INVENTORY_PURCHASE = {
    "purchase_date": "2026-05-13",
    "vendor": "Existing Tech Restore inventory acquisition",
    "reference_number": "TR-REAL-STOCK-20260513",
    "total_cost": 770.0,
    "notes": (
        "Received on 2026-05-13: 6 Kyocera E4610 units, 3 Kyocera E4810 units, and 2 LG Classic units. "
        "Approximate unit prices: E4610 $90 each, E4810 $60 each, LG Classic $25 each. "
        "Math: 6 x $90 = $540, 3 x $60 = $180, 2 x $25 = $50, total = $770."
    ),
    "items": [
        {"item_type": "device", "manufacturer": "Kyocera", "item_name": "E4610", "quantity": 6, "estimated_unit_cost": 90.0, "line_total": 540.0, "notes": "May 13, 2026 acquisition."},
        {"item_type": "device", "manufacturer": "Kyocera", "item_name": "E4810", "quantity": 3, "estimated_unit_cost": 60.0, "line_total": 180.0, "notes": "May 13, 2026 acquisition."},
        {"item_type": "device", "manufacturer": "LG", "item_name": "Classic", "quantity": 2, "estimated_unit_cost": 25.0, "line_total": 50.0, "notes": "May 13, 2026 acquisition."},
    ],
}


@dataclass
class ImportSummary:
    backup_path: str
    warnings: list[str] = field(default_factory=list)
    skipped_tables: list[str] = field(default_factory=list)
    protected_table_counts_before: dict[str, int] = field(default_factory=dict)
    protected_table_counts_after: dict[str, int] = field(default_factory=dict)
    tickets_deleted: int = 0
    ticket_dependent_records_deleted: dict[str, int] = field(default_factory=dict)
    hours_deleted: int = 0
    active_clock_sessions_deleted: int = 0
    voicemail_ticket_links_cleared: int = 0
    customers_created: int = 0
    customers_updated: int = 0
    tickets_inserted: int = 0
    hours_inserted: int = 0
    notes_inserted: int = 0
    pricing_notes_inserted: int = 0
    inventory_notes_result: str = "skipped"


def _normalize_phone(value: str | None) -> str:
    if not value:
        return ""
    return "".join(character for character in value if character.isdigit())


def _is_sqlite_database_url(database_url: str) -> bool:
    return not database_url or database_url.startswith("sqlite:///")


def _warn_for_non_persistent_path(db_path: Path) -> list[str]:
    normalized = db_path.as_posix()
    if any(normalized.startswith(prefix) for prefix in PERSISTENT_SQLITE_PREFIXES):
        return []
    return [
        "WARNING: database path does not look like Render persistent disk storage. "
        f"Resolved path: {db_path}"
    ]


def _list_tables(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {str(row["name"]) for row in rows}


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    return table_name in _list_tables(connection)


def _table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row["name"]) for row in rows}


def _scalar(connection: sqlite3.Connection, sql: str, parameters: tuple = ()) -> int:
    row = connection.execute(sql, parameters).fetchone()
    if row is None:
        return 0
    return int(row[0])


def _count_table(connection: sqlite3.Connection, table_name: str) -> int:
    return _scalar(connection, f"SELECT COUNT(*) FROM {table_name}")


def _count_where(connection: sqlite3.Connection, table_name: str, where_sql: str, parameters: tuple = ()) -> int:
    return _scalar(connection, f"SELECT COUNT(*) FROM {table_name} WHERE {where_sql}", parameters)


def _delete_all(connection: sqlite3.Connection, table_name: str, summary: ImportSummary, label: str) -> int:
    if not _table_exists(connection, table_name):
        summary.skipped_tables.append(f"{table_name} (missing)")
        return 0
    count = _count_table(connection, table_name)
    if count:
        connection.execute(f"DELETE FROM {table_name}")
    if label == "technician_hours":
        summary.hours_deleted = count
    else:
        summary.ticket_dependent_records_deleted[label] = count
    return count


def _delete_where(connection: sqlite3.Connection, table_name: str, where_sql: str, parameters: tuple, summary: ImportSummary, label: str) -> int:
    if not _table_exists(connection, table_name):
        summary.skipped_tables.append(f"{table_name} (missing)")
        return 0
    count = _count_where(connection, table_name, where_sql, parameters)
    if count:
        connection.execute(f"DELETE FROM {table_name} WHERE {where_sql}", parameters)
    summary.ticket_dependent_records_deleted[label] = count
    return count


def _update_where(
    connection: sqlite3.Connection,
    table_name: str,
    set_sql: str,
    where_sql: str,
    count_parameters: tuple,
    update_parameters: tuple,
    summary: ImportSummary,
    label: str,
) -> int:
    if not _table_exists(connection, table_name):
        summary.skipped_tables.append(f"{table_name} (missing)")
        return 0
    count = _count_where(connection, table_name, where_sql, count_parameters)
    if count:
        connection.execute(f"UPDATE {table_name} SET {set_sql} WHERE {where_sql}", update_parameters)
    if label == "voicemail_ticket_links_cleared":
        summary.voicemail_ticket_links_cleared = count
    else:
        summary.ticket_dependent_records_deleted[label] = count
    return count


def _placeholders(values: list[int]) -> str:
    return ", ".join("?" for _ in values)


def _fetch_ids(connection: sqlite3.Connection, table_name: str) -> list[int]:
    if not _table_exists(connection, table_name):
        return []
    rows = connection.execute(f"SELECT id FROM {table_name} ORDER BY id ASC").fetchall()
    return [int(row["id"]) for row in rows]


def _record_protected_counts(connection: sqlite3.Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table_name in (
        "users",
        "auth_invites",
        "twilio_settings",
        "pricing_defaults",
        "status_workflow_rules",
        "voicemail_records",
    ):
        if _table_exists(connection, table_name):
            counts[table_name] = _count_table(connection, table_name)
    return counts


def _wipe_ticket_and_hour_data(connection: sqlite3.Connection, summary: ImportSummary) -> None:
    ticket_ids = _fetch_ids(connection, "repair_tickets")
    repair_action_ids = _fetch_ids(connection, "repair_actions")
    ticket_id_placeholders = _placeholders(ticket_ids) if ticket_ids else ""
    repair_action_placeholders = _placeholders(repair_action_ids) if repair_action_ids else ""

    if _table_exists(connection, "technician_clock_sessions"):
        summary.active_clock_sessions_deleted = _count_where(
            connection,
            "technician_clock_sessions",
            "status = 'active' OR clocked_out_at IS NULL",
        )

    if ticket_ids and _table_exists(connection, "voicemail_records") and "ticket_id" in _table_columns(connection, "voicemail_records"):
        _update_where(
            connection,
            "voicemail_records",
            "ticket_id = NULL, updated_at = ?",
            f"ticket_id IN ({ticket_id_placeholders})",
            tuple(ticket_ids),
            (database.utc_now(), *ticket_ids),
            summary,
            "voicemail_ticket_links_cleared",
        )
    elif _table_exists(connection, "voicemail_records"):
        summary.voicemail_ticket_links_cleared = 0
    else:
        summary.skipped_tables.append("voicemail_records (missing)")

    if repair_action_ids:
        _delete_where(
            connection,
            "part_usage",
            f"repair_action_id IN ({repair_action_placeholders})",
            tuple(repair_action_ids),
            summary,
            "part_usage",
        )
    else:
        _delete_where(connection, "part_usage", "1 = 0", tuple(), summary, "part_usage")

    if _table_exists(connection, "inventory_movements"):
        movement_clauses: list[str] = []
        movement_params: list[int] = []
        if ticket_ids:
            movement_clauses.append(f"ticket_id IN ({ticket_id_placeholders})")
            movement_params.extend(ticket_ids)
        if repair_action_ids:
            movement_clauses.append(f"repair_action_id IN ({repair_action_placeholders})")
            movement_params.extend(repair_action_ids)
        where_sql = " OR ".join(movement_clauses) if movement_clauses else "1 = 0"
        _delete_where(connection, "inventory_movements", where_sql, tuple(movement_params), summary, "inventory_movements")
    else:
        summary.skipped_tables.append("inventory_movements (missing)")

    if _table_exists(connection, "attachments"):
        attachment_params: list[object] = []
        attachment_clauses: list[str] = []
        if ticket_ids:
            attachment_clauses.append(
                f"(LOWER(entity_type) IN ({', '.join('?' for _ in TICKET_ENTITY_TYPES)}) AND entity_id IN ({ticket_id_placeholders}))"
            )
            attachment_params.extend(sorted(TICKET_ENTITY_TYPES))
            attachment_params.extend(ticket_ids)
        if repair_action_ids:
            attachment_clauses.append(
                f"(LOWER(entity_type) IN ({', '.join('?' for _ in REPAIR_ACTION_ENTITY_TYPES)}) AND entity_id IN ({repair_action_placeholders}))"
            )
            attachment_params.extend(sorted(REPAIR_ACTION_ENTITY_TYPES))
            attachment_params.extend(repair_action_ids)
        _delete_where(
            connection,
            "attachments",
            " OR ".join(attachment_clauses) if attachment_clauses else "1 = 0",
            tuple(attachment_params),
            summary,
            "attachments",
        )
    else:
        summary.skipped_tables.append("attachments (missing)")

    if _table_exists(connection, "activity_logs"):
        placeholders = ", ".join("?" for _ in ACTIVITY_LOG_ENTITY_TYPES)
        _delete_where(
            connection,
            "activity_logs",
            f"LOWER(entity_type) IN ({placeholders})",
            tuple(sorted(ACTIVITY_LOG_ENTITY_TYPES)),
            summary,
            "activity_logs",
        )
    else:
        summary.skipped_tables.append("activity_logs (missing)")

    if ticket_ids:
        _delete_where(connection, "loaner_checkouts", f"ticket_id IN ({ticket_id_placeholders})", tuple(ticket_ids), summary, "loaner_checkouts")
        _delete_where(connection, "ticket_notes", f"ticket_id IN ({ticket_id_placeholders})", tuple(ticket_ids), summary, "ticket_notes")
        _delete_where(connection, "ticket_status_history", f"ticket_id IN ({ticket_id_placeholders})", tuple(ticket_ids), summary, "ticket_status_history")
        _delete_where(connection, "repair_actions", f"ticket_id IN ({ticket_id_placeholders})", tuple(ticket_ids), summary, "repair_actions")
    else:
        _delete_where(connection, "loaner_checkouts", "1 = 0", tuple(), summary, "loaner_checkouts")
        _delete_where(connection, "ticket_notes", "1 = 0", tuple(), summary, "ticket_notes")
        _delete_where(connection, "ticket_status_history", "1 = 0", tuple(), summary, "ticket_status_history")
        _delete_where(connection, "repair_actions", "1 = 0", tuple(), summary, "repair_actions")

    _delete_all(connection, "technician_hours", summary, "technician_hours")
    _delete_all(connection, "technician_clock_sessions", summary, "technician_clock_sessions")

    if _table_exists(connection, "repair_tickets"):
        summary.tickets_deleted = _count_table(connection, "repair_tickets")
        if summary.tickets_deleted:
            connection.execute("DELETE FROM repair_tickets")
    else:
        summary.skipped_tables.append("repair_tickets (missing)")


def _merge_notes(existing: str | None, addition: str | None) -> str | None:
    existing_text = (existing or "").strip()
    addition_text = (addition or "").strip()
    if not addition_text:
        return existing_text or None
    if not existing_text:
        return addition_text
    if addition_text in existing_text:
        return existing_text
    return f"{existing_text}\n\n{addition_text}"


def _find_customer(connection: sqlite3.Connection, full_name: str, phone: str | None) -> sqlite3.Row | None:
    normalized_phone = _normalize_phone(phone)
    rows = connection.execute(
        """
        SELECT id, full_name, primary_phone, notes, created_at, updated_at
        FROM customers
        WHERE LOWER(full_name) = LOWER(?)
           OR COALESCE(primary_phone, '') = COALESCE(?, '')
        ORDER BY id ASC
        """,
        (full_name, phone),
    ).fetchall()
    if not rows:
        return None
    for row in rows:
        if normalized_phone and _normalize_phone(row["primary_phone"]) == normalized_phone:
            return row
    for row in rows:
        if str(row["full_name"]).strip().lower() == full_name.strip().lower():
            return row
    return rows[0]


def _upsert_customers(connection: sqlite3.Connection, summary: ImportSummary) -> dict[tuple[str, str], int]:
    customer_ids: dict[tuple[str, str], int] = {}
    for customer in REAL_CUSTOMERS:
        full_name = customer["full_name"]
        phone = customer["phone"]
        notes = customer["notes"]
        key = (full_name, _normalize_phone(phone))
        existing = _find_customer(connection, full_name, phone)
        if existing is None:
            timestamp = database.utc_now()
            cursor = connection.execute(
                """
                INSERT INTO customers (full_name, primary_phone, alternate_phone, email, notes, created_at, updated_at)
                VALUES (?, ?, NULL, NULL, ?, ?, ?)
                """,
                (full_name, phone, notes, timestamp, timestamp),
            )
            customer_ids[key] = int(cursor.lastrowid)
            summary.customers_created += 1
            continue

        next_phone = phone or existing["primary_phone"]
        next_notes = _merge_notes(existing["notes"], notes)
        connection.execute(
            """
            UPDATE customers
            SET full_name = ?,
                primary_phone = ?,
                notes = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (full_name, next_phone, next_notes, database.utc_now(), int(existing["id"])),
        )
        customer_ids[key] = int(existing["id"])
        summary.customers_updated += 1
    return customer_ids


def _insert_ticket_records(connection: sqlite3.Connection, customer_ids: dict[tuple[str, str], int], summary: ImportSummary) -> dict[str, int]:
    ticket_ids: dict[str, int] = {}
    for ticket in REAL_TICKETS:
        customer_key = (ticket["customer_name"], _normalize_phone(ticket["phone"]))
        customer_id = customer_ids[customer_key]
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
            ) VALUES (?, ?, NULL, ?, NULL, NULL, NULL, NULL, ?, ?, ?, ?, 'unknown', 'unknown', 'unknown', 'unknown', NULL, 0, 0, ?, ?, ?, 0, ?, 'normal', 'Mattis', 'Mattis', ?, ?, ?)
            """,
            (
                ticket["ticket_number"],
                customer_id,
                ticket["device"],
                ticket["status"],
                ticket["issue_category"],
                ticket["issue_description"],
                ticket["condition_summary"],
                ticket["estimated_price"],
                ticket["final_price"],
                ticket["payment_status"],
                ticket["status"],
                ticket["intake_date"],
                ticket["created_at"],
                ticket["updated_at"],
            ),
        )
        ticket_id = int(cursor.lastrowid)
        ticket_ids[ticket["ticket_number"]] = ticket_id
        summary.tickets_inserted += 1

        for old_status, new_status, changed_by, note, created_at in ticket["status_history"]:
            connection.execute(
                """
                INSERT INTO ticket_status_history (ticket_id, old_status, new_status, changed_by, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (ticket_id, old_status, new_status, changed_by, note, created_at),
            )

        for note_type, body, created_by, created_at in ticket["notes"]:
            connection.execute(
                """
                INSERT INTO ticket_notes (ticket_id, note_type, body, created_by, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (ticket_id, note_type, body, created_by, created_at),
            )
            summary.notes_inserted += 1
            if note_type == "pricing":
                summary.pricing_notes_inserted += 1

    return ticket_ids


def _insert_hours(connection: sqlite3.Connection, ticket_ids: dict[str, int], summary: ImportSummary) -> None:
    for entry in REAL_HOURS:
        if entry["hours_worked"] <= 0:
            continue
        ticket_id = ticket_ids.get(entry["ticket_number"]) if entry["ticket_number"] else None
        timestamp = f"{entry['work_date']}T12:00:00+00:00"
        connection.execute(
            """
            INSERT INTO technician_hours (
                ticket_id,
                technician,
                work_date,
                hours_worked,
                work_description,
                created_at,
                updated_at
            ) VALUES (?, 'Mattis', ?, ?, ?, ?, ?)
            """,
            (ticket_id, entry["work_date"], float(entry["hours_worked"]), entry["work_description"], timestamp, timestamp),
        )
        summary.hours_inserted += 1


def _upsert_inventory_purchase(connection: sqlite3.Connection, summary: ImportSummary) -> None:
    if not _table_exists(connection, "inventory_purchases") or not _table_exists(connection, "inventory_purchase_items"):
        summary.inventory_notes_result = "skipped (inventory purchase tables missing)"
        return

    existing = connection.execute(
        "SELECT id FROM inventory_purchases WHERE reference_number = ? LIMIT 1",
        (INVENTORY_PURCHASE["reference_number"],),
    ).fetchone()
    timestamp = database.utc_now()
    if existing is None:
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
                INVENTORY_PURCHASE["purchase_date"],
                INVENTORY_PURCHASE["vendor"],
                INVENTORY_PURCHASE["reference_number"],
                INVENTORY_PURCHASE["total_cost"],
                INVENTORY_PURCHASE["notes"],
                timestamp,
                timestamp,
            ),
        )
        purchase_id = int(cursor.lastrowid)
        action = "inserted"
    else:
        purchase_id = int(existing["id"])
        connection.execute(
            """
            UPDATE inventory_purchases
            SET purchase_date = ?,
                vendor = ?,
                total_cost = ?,
                notes = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                INVENTORY_PURCHASE["purchase_date"],
                INVENTORY_PURCHASE["vendor"],
                INVENTORY_PURCHASE["total_cost"],
                INVENTORY_PURCHASE["notes"],
                timestamp,
                purchase_id,
            ),
        )
        connection.execute("DELETE FROM inventory_purchase_items WHERE purchase_id = ?", (purchase_id,))
        action = "updated"

    for item in INVENTORY_PURCHASE["items"]:
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
                item["item_type"],
                item["manufacturer"],
                item["item_name"],
                item["quantity"],
                item["estimated_unit_cost"],
                item["line_total"],
                item["notes"],
                timestamp,
                timestamp,
            ),
        )

    summary.inventory_notes_result = f"{action} inventory purchase note with {len(INVENTORY_PURCHASE['items'])} purchase item rows"


def _assert_protected_tables_unchanged(summary: ImportSummary) -> None:
    for table_name, before_count in summary.protected_table_counts_before.items():
        after_count = summary.protected_table_counts_after.get(table_name)
        if after_count != before_count:
            raise RuntimeError(
                f"Protected table count changed for {table_name}: before={before_count}, after={after_count}"
            )


def _validate_import(connection: sqlite3.Connection) -> None:
    ticket_count = _count_table(connection, "repair_tickets")
    hours_count = _count_table(connection, "technician_hours")
    total_hours_row = connection.execute(
        "SELECT ROUND(COALESCE(SUM(hours_worked), 0), 2) FROM technician_hours"
    ).fetchone()
    total_hours = float(total_hours_row[0]) if total_hours_row is not None else 0.0

    if ticket_count != 4:
        raise RuntimeError(f"Expected 4 real tickets after import, found {ticket_count}")
    if hours_count != 10:
        raise RuntimeError(f"Expected 10 real hour entries after import, found {hours_count}")
    if round(total_hours, 2) != 14.0:
        raise RuntimeError(f"Expected 14.00 total hours after import, found {total_hours:.2f}")

    zero_hour_count = _count_where(connection, "technician_hours", "hours_worked <= 0")
    if zero_hour_count != 0:
        raise RuntimeError("Zero-hour technician entries remain after import")

    may_11_count = _count_where(connection, "technician_hours", "work_date = ?", ("2026-05-11",))
    if may_11_count != 0:
        raise RuntimeError("Unexpected May 11 technician-hours entry remains after import")

    yossi_weiss = connection.execute(
        """
        SELECT rt.final_price, rt.payment_status, tn.body
        FROM repair_tickets rt
        JOIN customers c ON c.id = rt.customer_id
        LEFT JOIN ticket_notes tn ON tn.ticket_id = rt.id AND tn.note_type = 'pricing'
        WHERE c.full_name = 'Yossi Weiss'
        ORDER BY tn.id ASC
        LIMIT 1
        """
    ).fetchone()
    if yossi_weiss is None or float(yossi_weiss["final_price"]) != 25.0 or yossi_weiss["payment_status"] != "unpaid":
        raise RuntimeError("Yossi Weiss validation failed")
    if "$35" not in str(yossi_weiss["body"]):
        raise RuntimeError("Yossi Weiss pricing note did not preserve the $35 standard price")

    ungar = connection.execute(
        """
        SELECT rt.final_price, rt.payment_status, GROUP_CONCAT(tn.body, '\n') AS notes_blob
        FROM repair_tickets rt
        JOIN customers c ON c.id = rt.customer_id
        LEFT JOIN ticket_notes tn ON tn.ticket_id = rt.id
        WHERE c.full_name = 'Ungar'
        GROUP BY rt.id, rt.final_price, rt.payment_status
        LIMIT 1
        """
    ).fetchone()
    if ungar is None or float(ungar["final_price"]) != 0.0 or ungar["payment_status"] != "paid":
        raise RuntimeError("Ungar validation failed")
    if "$85" not in str(ungar["notes_blob"]) or "on the house" not in str(ungar["notes_blob"]).lower():
        raise RuntimeError("Ungar notes did not preserve the standard $85 / on-the-house wording")

    unknown_screen = connection.execute(
        """
        SELECT c.primary_phone, rt.device_model_text_override, rt.status
        FROM repair_tickets rt
        JOIN customers c ON c.id = rt.customer_id
        WHERE c.full_name = 'Unknown Screen Customer'
        LIMIT 1
        """
    ).fetchone()
    if unknown_screen is None:
        raise RuntimeError("Unknown Screen Customer validation failed")
    if unknown_screen["primary_phone"] != "732-237-4070":
        raise RuntimeError("Unknown Screen Customer phone mismatch")
    if "Samsung Galaxy A13 5G / SM-A136U1" not in str(unknown_screen["device_model_text_override"]):
        raise RuntimeError("Unknown Screen Customer device/model mismatch")

    yossi_toder = connection.execute(
        """
        SELECT c.primary_phone, rt.final_price, rt.status
        FROM repair_tickets rt
        JOIN customers c ON c.id = rt.customer_id
        WHERE c.full_name = 'Yossi Toder'
        LIMIT 1
        """
    ).fetchone()
    if yossi_toder is None or yossi_toder["primary_phone"] != "732-664-1835":
        raise RuntimeError("Yossi Toder phone mismatch")
    if float(yossi_toder["final_price"]) != 0.0 or yossi_toder["status"] != "Customer Declined":
        raise RuntimeError("Yossi Toder declined/no-charge validation failed")


def run_real_data_reset_import() -> ImportSummary:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not _is_sqlite_database_url(database_url):
        raise RuntimeError(
            "This script only supports SQLite DATABASE_URL values. "
            f"Received DATABASE_URL={database_url!r}"
        )

    db_path = Path(database.DB_PATH)
    if not db_path.exists():
        raise RuntimeError(
            "Resolved SQLite database path does not exist. "
            f"Expected existing file at {db_path}"
        )

    warnings = _warn_for_non_persistent_path(db_path)
    backup = database.create_database_backup()
    summary = ImportSummary(backup_path=str(backup["backup_path"]), warnings=warnings)

    with database.get_connection() as connection:
        connection.execute("BEGIN")
        try:
            summary.protected_table_counts_before = _record_protected_counts(connection)
            _wipe_ticket_and_hour_data(connection, summary)
            customer_ids = _upsert_customers(connection, summary)
            ticket_ids = _insert_ticket_records(connection, customer_ids, summary)
            _insert_hours(connection, ticket_ids, summary)
            _upsert_inventory_purchase(connection, summary)
            summary.protected_table_counts_after = _record_protected_counts(connection)
            _assert_protected_tables_unchanged(summary)
            _validate_import(connection)
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    return summary


def _print_summary(summary: ImportSummary) -> None:
    print(f"Backup created: {summary.backup_path}")
    for warning in summary.warnings:
        print(warning)
    print(f"Tickets deleted: {summary.tickets_deleted}")
    print(
        "Ticket-dependent records deleted: "
        f"{sum(summary.ticket_dependent_records_deleted.values())} "
        f"{summary.ticket_dependent_records_deleted}"
    )
    print(f"Hours deleted: {summary.hours_deleted}")
    print(f"Active clock sessions deleted: {summary.active_clock_sessions_deleted}")
    print(f"Voicemail ticket links cleared: {summary.voicemail_ticket_links_cleared}")
    print(f"Customers created: {summary.customers_created}")
    print(f"Customers updated: {summary.customers_updated}")
    print(f"Tickets inserted: {summary.tickets_inserted}")
    print(f"Hours inserted: {summary.hours_inserted}")
    print(f"Notes inserted: {summary.notes_inserted}")
    print(f"Pricing notes inserted: {summary.pricing_notes_inserted}")
    print(f"Inventory notes result: {summary.inventory_notes_result}")
    if summary.skipped_tables:
        print(f"Skipped tables: {sorted(set(summary.skipped_tables))}")
    print(f"Hours total check: 14.00 hours @ ${HOURLY_RATE:.2f}/hour = ${14 * HOURLY_RATE:.2f}")
    print("Protected tables preserved: auth users, invites, settings, Twilio settings, voicemail records row count")


def main() -> int:
    summary = run_real_data_reset_import()
    _print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())