from __future__ import annotations

import sqlite3


REAL_SEED_CUSTOMERS = [
    {
        "full_name": "Yossi Weiss",
        "phone": "732-670-6635",
        "notes": "Repeat/frequent customer; works for TAG.",
        "jobs": [
            {
                "ticket_number": "TR-00001",
                "legacy_ticket_number": "TR-REAL-20260507-01",
                "device": "Wonder phone",
                "issue_category": "Touchpad replacement",
                "issue_description": "Touchpad replacement using a customer-supplied part.",
                "condition_summary": "Customer supplied part. About 20 minutes of bench time.",
                "estimated_price": 25.0,
                "final_price": 25.0,
                "payment_status": "unpaid",
                "status": "Picked Up / Closed",
                "intake_date": "2026-05-07T12:00:00+00:00",
                "created_at": "2026-05-07T12:00:00+00:00",
                "updated_at": "2026-05-07T12:20:00+00:00",
                "status_history": [
                    (None, "New Intake", "Mattis", "Real Tech Restore import: initial intake.", "2026-05-07T12:00:00+00:00"),
                    (
                        "New Intake",
                        "Picked Up / Closed",
                        "Mattis",
                        "Touchpad replacement completed. Customer still owes $25. The older $30 amount was not used.",
                        "2026-05-07T12:20:00+00:00",
                    ),
                ],
                "notes": [
                    ("front_desk", "First Tech Restore customer repair. Customer supplied the part for a Wonder phone touchpad replacement.", "Mattis", "2026-05-07T12:02:00+00:00"),
                    ("pricing", "Standard price would be $35. Actual charge is $25. Do not use the older $30 amount.", "Mattis", "2026-05-07T12:05:00+00:00"),
                    ("parts", "Customer supplied the replacement part.", "Mattis", "2026-05-07T12:06:00+00:00"),
                    ("technician", "Completed in about 20 minutes and verified touch response before release.", "Mattis", "2026-05-07T12:18:00+00:00"),
                ],
            },
            {
                "ticket_number": "TR-00002",
                "legacy_ticket_number": "TR-REAL-20260603-01",
                "device": "Fusion phone, model F2",
                "issue_category": "Screen replacement",
                "issue_description": "Screen replacement using a customer-supplied part.",
                "condition_summary": "Customer supplied part.",
                "estimated_price": 25.0,
                "final_price": 25.0,
                "payment_status": "unpaid",
                "status": "Picked Up / Closed",
                "intake_date": "2026-06-03T12:00:00+00:00",
                "created_at": "2026-06-03T12:00:00+00:00",
                "updated_at": "2026-06-03T12:25:00+00:00",
                "status_history": [
                    (None, "New Intake", "Mattis", "Real Tech Restore import: initial intake.", "2026-06-03T12:00:00+00:00"),
                    ("New Intake", "Picked Up / Closed", "Mattis", "Screen replacement completed using the customer-supplied part.", "2026-06-03T12:25:00+00:00"),
                ],
                "notes": [
                    ("front_desk", "Fusion phone, model F2 screen replacement using a customer-supplied part.", "Mattis", "2026-06-03T12:02:00+00:00"),
                    ("parts", "Customer supplied the replacement part.", "Mattis", "2026-06-03T12:05:00+00:00"),
                    ("pricing", "Actual charge is $25.", "Mattis", "2026-06-03T12:10:00+00:00"),
                ],
            },
            {
                "ticket_number": "TR-00003",
                "legacy_ticket_number": "TR-REAL-20260603-02",
                "device": "Lenovo IdeaPad 5 2-in-1 14Q8X9 ARM/Snapdragon laptop",
                "issue_category": "BitLocker / Windows update boot loop issue",
                "issue_description": "BitLocker / Windows update boot loop issue.",
                "condition_summary": "Created Windows 11 ARM64 USB, booted with Secure Boot temporarily disabled, ran DISM RevertPendingActions, disabled BitLocker protectors temporarily, renamed SoftwareDistribution and catroot2, ran SFC with no integrity violations, removed/reverted pending update actions, and got the computer repaired enough to reach Windows sign-in.",
                "estimated_price": 75.0,
                "final_price": None,
                "payment_status": "unpaid",
                "status": "In Repair",
                "intake_date": "2026-06-03T12:00:00+00:00",
                "created_at": "2026-06-03T12:00:00+00:00",
                "updated_at": "2026-06-03T13:00:00+00:00",
                "status_history": [
                    (None, "New Intake", "Mattis", "Real Tech Restore import: initial intake.", "2026-06-03T12:00:00+00:00"),
                    ("New Intake", "In Repair", "Mattis", "Work reached Windows sign-in but the job was not closed out.", "2026-06-03T13:00:00+00:00"),
                ],
                "notes": [
                    ("technician", "Created Windows 11 ARM64 USB, disabled Secure Boot temporarily, ran DISM RevertPendingActions, disabled BitLocker protectors temporarily, renamed SoftwareDistribution and catroot2, ran SFC with no integrity violations, and reached Windows sign-in.", "Mattis", "2026-06-03T12:45:00+00:00"),
                    ("pricing", "Charge is $75 when completed. Do not count it as a confirmed owed balance until the job is marked completed.", "Mattis", "2026-06-03T12:50:00+00:00"),
                ],
            },
        ],
    },
    {
        "full_name": "Yossi Toder",
        "phone": "732-664-1835",
        "notes": None,
        "jobs": [
            {
                "ticket_number": "TR-00004",
                "legacy_ticket_number": "TR-REAL-20260513-01",
                "device": "Alcatel 4044T",
                "issue_category": "Not reading SIM card",
                "issue_description": "Not reading SIM card.",
                "condition_summary": "SIM reader damaged; adjusted and tested with SIM.",
                "estimated_price": 0.0,
                "final_price": 0.0,
                "payment_status": "paid",
                "status": "Customer Declined",
                "intake_date": "2026-05-13T12:00:00+00:00",
                "created_at": "2026-05-13T12:00:00+00:00",
                "updated_at": "2026-05-13T12:30:00+00:00",
                "status_history": [
                    (None, "New Intake", "Mattis", "Real Tech Restore import: initial intake.", "2026-05-13T12:00:00+00:00"),
                    ("New Intake", "Customer Declined", "Mattis", "SIM reader was damaged. Customer declined any complicated or expensive repair.", "2026-05-13T12:30:00+00:00"),
                ],
                "notes": [
                    ("front_desk", "SIM reader damaged.", "Mattis", "2026-05-13T12:03:00+00:00"),
                    ("technician", "Adjusted and tested with SIM. Device still did not read the SIM card.", "Mattis", "2026-05-13T12:20:00+00:00"),
                    ("pricing", "No charge.", "Mattis", "2026-05-13T12:24:00+00:00"),
                ],
            }
        ],
    },
    {
        "full_name": "Ungar",
        "phone": "732-363-3950",
        "notes": None,
        "jobs": [
            {
                "ticket_number": "TR-00005",
                "legacy_ticket_number": "TR-REAL-UNKNOWN-01",
                "device": "Kyocera E4810",
                "issue_category": "White screen / screen replacement",
                "issue_description": "White screen / screen replacement.",
                "condition_summary": "On the house because TAG sold the phone.",
                "estimated_price": 85.0,
                "final_price": 0.0,
                "payment_status": "paid",
                "status": "Picked Up / Closed",
                "intake_date": "unknown",
                "created_at": "2026-06-15T12:00:00+00:00",
                "updated_at": "2026-06-15T12:30:00+00:00",
                "status_history": [
                    (None, "New Intake", "Mattis", "Real Tech Restore import: initial intake.", "2026-06-15T12:00:00+00:00"),
                    ("New Intake", "Picked Up / Closed", "Mattis", "Screen replacement completed on the house because TAG sold the phone.", "2026-06-15T12:30:00+00:00"),
                ],
                "notes": [
                    ("front_desk", "On the house because TAG sold the phone.", "Mattis", "2026-06-15T12:05:00+00:00"),
                    ("pricing", "Normal screen-only charge is $85. Actual charge is $0.", "Mattis", "2026-06-15T12:10:00+00:00"),
                    ("technician", "Screen replacement completed.", "Mattis", "2026-06-15T12:25:00+00:00"),
                ],
            }
        ],
    },
    {
        "full_name": "Unknown Screen Customer",
        "phone": "732-237-4070",
        "notes": None,
        "jobs": [
            {
                "ticket_number": "TR-00006",
                "legacy_ticket_number": "TR-REAL-20260525-01",
                "device": "Samsung Galaxy A13 5G / SM-A136U1",
                "issue_category": "Screen repair needed",
                "issue_description": "Customer needed the correct screen with frame for a Samsung Galaxy A13 5G / SM-A136U1.",
                "condition_summary": "Customer declined the repair.",
                "estimated_price": 0.0,
                "final_price": 0.0,
                "payment_status": "paid",
                "status": "Customer Declined",
                "intake_date": "2026-05-25T12:00:00+00:00",
                "created_at": "2026-05-25T12:00:00+00:00",
                "updated_at": "2026-05-25T12:40:00+00:00",
                "status_history": [
                    (None, "New Intake", "Mattis", "Real Tech Restore import: initial intake.", "2026-05-25T12:00:00+00:00"),
                    ("New Intake", "Customer Declined", "Mattis", "Correct model identified and the customer decided not to move forward with the repair.", "2026-05-25T12:40:00+00:00"),
                ],
                "notes": [
                    ("front_desk", "This was a screen repair request.", "Mattis", "2026-05-25T12:03:00+00:00"),
                    ("technician", "Identified the correct model as Samsung Galaxy A13 5G / SM-A136U1 and confirmed the job needed the correct screen with frame.", "Mattis", "2026-05-25T12:15:00+00:00"),
                    ("pricing", "No charge because the customer declined the repair before any paid work was authorized.", "Mattis", "2026-05-25T12:20:00+00:00"),
                ],
            }
        ],
    },
    {
        "full_name": "Miriam Drew",
        "phone": "732-534-0820",
        "notes": None,
        "jobs": [
            {
                "ticket_number": "TR-00007",
                "legacy_ticket_number": "TR-REAL-UNKNOWN-02",
                "device": "Canon SX740",
                "issue_category": "Screen not working",
                "issue_description": "Screen not working.",
                "condition_summary": "Screen cable replacement.",
                "estimated_price": 75.0,
                "final_price": 75.0,
                "payment_status": "paid",
                "status": "Picked Up / Closed",
                "intake_date": "unknown",
                "created_at": "2026-06-15T12:00:00+00:00",
                "updated_at": "2026-06-15T12:35:00+00:00",
                "status_history": [
                    (None, "New Intake", "Mattis", "Real Tech Restore import: initial intake.", "2026-06-15T12:00:00+00:00"),
                    ("New Intake", "Picked Up / Closed", "Mattis", "Screen cable replacement completed.", "2026-06-15T12:35:00+00:00"),
                ],
                "notes": [
                    ("front_desk", "Screen not working.", "Mattis", "2026-06-15T12:03:00+00:00"),
                    ("parts", "Part cost: $25.", "Mattis", "2026-06-15T12:08:00+00:00"),
                    ("pricing", "Charge is $75.", "Mattis", "2026-06-15T12:10:00+00:00"),
                    ("internal", "This job was previously unpaid but the latest status is paid.", "Mattis", "2026-06-15T12:15:00+00:00"),
                ],
            }
        ],
    },
    {
        "full_name": "Globerman",
        "phone": "347-262-7894",
        "notes": None,
        "jobs": [
            {
                "ticket_number": "TR-00008",
                "legacy_ticket_number": "TR-REAL-UNKNOWN-03",
                "device": "TCL",
                "issue_category": "White screen / shell job",
                "issue_description": "White screen / shell job.",
                "condition_summary": "No battery needed. TAG discount applied.",
                "estimated_price": 110.0,
                "final_price": 100.0,
                "payment_status": "paid",
                "status": "Picked Up / Closed",
                "intake_date": "unknown",
                "created_at": "2026-06-15T12:00:00+00:00",
                "updated_at": "2026-06-15T12:35:00+00:00",
                "status_history": [
                    (None, "New Intake", "Mattis", "Real Tech Restore import: initial intake.", "2026-06-15T12:00:00+00:00"),
                    ("New Intake", "Picked Up / Closed", "Mattis", "White screen shell job completed with TAG discount applied.", "2026-06-15T12:35:00+00:00"),
                ],
                "notes": [
                    ("front_desk", "White screen / shell job.", "Mattis", "2026-06-15T12:03:00+00:00"),
                    ("parts", "Part/shell cost: $90. No battery needed.", "Mattis", "2026-06-15T12:08:00+00:00"),
                    ("pricing", "Normal charge is $110. Actual charge is $100.", "Mattis", "2026-06-15T12:10:00+00:00"),
                    ("internal", "Payment method: check.", "Mattis", "2026-06-15T12:15:00+00:00"),
                ],
            }
        ],
    },
    {
        "full_name": "Miriam Braun",
        "phone": "646-468-8833",
        "notes": None,
        "jobs": [
            {
                "ticket_number": "TR-00009",
                "legacy_ticket_number": "TR-REAL-UNKNOWN-04",
                "device": "Dell XPS laptop",
                "issue_category": "Screen replacement",
                "issue_description": "Needs screen replacement.",
                "condition_summary": "Part found and ordered; part coming.",
                "estimated_price": None,
                "final_price": None,
                "payment_status": "unpaid",
                "status": "Waiting for Parts",
                "intake_date": "unknown",
                "created_at": "2026-06-15T12:00:00+00:00",
                "updated_at": "2026-06-15T12:40:00+00:00",
                "status_history": [
                    (None, "New Intake", "Mattis", "Real Tech Restore import: initial intake.", "2026-06-15T12:00:00+00:00"),
                    ("New Intake", "Waiting for Parts", "Mattis", "Part found and ordered; part coming.", "2026-06-15T12:40:00+00:00"),
                ],
                "notes": [
                    ("front_desk", "Screen replacement needed.", "Mattis", "2026-06-15T12:03:00+00:00"),
                    ("parts", "Need exact replacement and the job is not completed yet.", "Mattis", "2026-06-15T12:10:00+00:00"),
                    ("internal", "Final charge/payment not recorded yet.", "Mattis", "2026-06-15T12:15:00+00:00"),
                ],
            }
        ],
    },
    {
        "full_name": "Unknown / walk-in",
        "phone": None,
        "notes": "Customer name and phone number were not collected.",
        "jobs": [
            {
                "ticket_number": "TR-00010",
                "legacy_ticket_number": "TR-REAL-20260615-01",
                "device": "Kyocera 4810",
                "issue_category": "Back bottom piece replacement",
                "issue_description": "Replaced the back bottom piece where the back screw anchors.",
                "condition_summary": "Payment by credit card through one of the TAG technicians.",
                "estimated_price": 35.0,
                "final_price": 35.0,
                "payment_status": "paid",
                "status": "Picked Up / Closed",
                "intake_date": "2026-06-15T12:00:00+00:00",
                "created_at": "2026-06-15T12:00:00+00:00",
                "updated_at": "2026-06-15T12:25:00+00:00",
                "status_history": [
                    (None, "New Intake", "Mattis", "Real Tech Restore import: initial intake.", "2026-06-15T12:00:00+00:00"),
                    ("New Intake", "Picked Up / Closed", "Mattis", "Back bottom piece replacement completed.", "2026-06-15T12:25:00+00:00"),
                ],
                "notes": [
                    ("front_desk", "Customer name and phone number were not collected.", "Mattis", "2026-06-15T12:03:00+00:00"),
                    ("pricing", "Charge is $35.", "Mattis", "2026-06-15T12:08:00+00:00"),
                    ("internal", "Paid by credit card through one of the TAG technicians.", "Mattis", "2026-06-15T12:15:00+00:00"),
                ],
            }
        ],
    },
    {
        "full_name": "Dorfman",
        "phone": "732-267-3589",
        "notes": None,
        "jobs": [
            {
                "ticket_number": "TR-00011",
                "legacy_ticket_number": "TR-REAL-20260615-02",
                "device": "HP OmniBook laptop",
                "issue_category": "Broken screen",
                "issue_description": "Broken screen.",
                "condition_summary": "New intake / diagnosing / part not ordered yet.",
                "estimated_price": None,
                "final_price": None,
                "payment_status": "unpaid",
                "status": "New Intake",
                "intake_date": "2026-06-15T12:00:00+00:00",
                "created_at": "2026-06-15T12:00:00+00:00",
                "updated_at": "2026-06-15T12:00:00+00:00",
                "status_history": [
                    (None, "New Intake", "Mattis", "Real Tech Restore import: initial intake.", "2026-06-15T12:00:00+00:00"),
                ],
                "notes": [
                    ("front_desk", "HP OmniBook laptop with a broken screen.", "Mattis", "2026-06-15T12:03:00+00:00"),
                    ("internal", "Need help ordering the part. Final cost not decided yet.", "Mattis", "2026-06-15T12:06:00+00:00"),
                    ("parts", "Screen details found from removed panel: Samsung panel model ATNA40KW02, H/W 0, CT XUMWA015GL757Q, HP SPS/LCD P48657-001, barcode text JW2580.", "Mattis", "2026-06-15T12:10:00+00:00"),
                ],
            }
        ],
    },
]


def _normalize_phone(value: str | None) -> str:
    if not value:
        return ""
    return "".join(character for character in value if character.isdigit())


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _delete_all(connection: sqlite3.Connection, table_name: str) -> None:
    if _table_exists(connection, table_name):
        connection.execute(f"DELETE FROM {table_name}")


def _delete_where(connection: sqlite3.Connection, table_name: str, where_sql: str, parameters: tuple = ()) -> None:
    if _table_exists(connection, table_name):
        connection.execute(f"DELETE FROM {table_name} WHERE {where_sql}", parameters)


def wipe_real_customer_job_data(connection: sqlite3.Connection) -> None:
    if _table_exists(connection, "voicemail_records") and _table_exists(connection, "repair_tickets"):
        connection.execute("UPDATE voicemail_records SET customer_id = NULL, ticket_id = NULL")

    _delete_all(connection, "technician_hours")
    _delete_all(connection, "ticket_notes")
    _delete_all(connection, "ticket_status_history")
    _delete_all(connection, "repair_actions")
    _delete_all(connection, "loaner_checkouts")
    _delete_all(connection, "part_usage")
    _delete_all(connection, "inventory_movements")
    _delete_all(connection, "attachments")
    _delete_all(connection, "repair_tickets")
    _delete_all(connection, "customers")


def _find_customer(connection: sqlite3.Connection, full_name: str, phone: str | None) -> sqlite3.Row | None:
    normalized_phone = _normalize_phone(phone)
    rows = connection.execute(
        """
        SELECT id, full_name, primary_phone, notes
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


def _upsert_customers(connection: sqlite3.Connection) -> dict[tuple[str, str], int]:
    customer_ids: dict[tuple[str, str], int] = {}
    timestamp = "2026-06-15T12:00:00+00:00"
    for customer in REAL_SEED_CUSTOMERS:
        full_name = customer["full_name"]
        phone = customer["phone"]
        key = (full_name, _normalize_phone(phone))
        existing = _find_customer(connection, full_name, phone)
        if existing is None:
            cursor = connection.execute(
                """
                INSERT INTO customers (full_name, primary_phone, alternate_phone, email, notes, created_at, updated_at)
                VALUES (?, ?, NULL, NULL, ?, ?, ?)
                """,
                (full_name, phone, customer["notes"], timestamp, timestamp),
            )
            customer_ids[key] = int(cursor.lastrowid)
            continue

        connection.execute(
            """
            UPDATE customers
            SET full_name = ?,
                primary_phone = ?,
                notes = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                full_name,
                phone or existing["primary_phone"],
                _merge_notes(existing["notes"], customer["notes"]),
                timestamp,
                int(existing["id"]),
            ),
        )
        customer_ids[key] = int(existing["id"])
    return customer_ids


def _delete_ticket_related_rows(connection: sqlite3.Connection, ticket_id: int) -> None:
    # Only delete from tables that exist and have ticket_id column
    tables_to_clean = [
        "ticket_notes",
        "ticket_status_history",
    ]
    
    for table_name in tables_to_clean:
        try:
            _delete_where(connection, table_name, "ticket_id = ?", (ticket_id,))
        except Exception:
            # Table may not exist yet, skip
            pass


def _find_existing_seed_ticket(connection: sqlite3.Connection, ticket: dict) -> sqlite3.Row | None:
    legacy_ticket_number = ticket.get("legacy_ticket_number")
    candidate_numbers = [ticket["ticket_number"]]
    if legacy_ticket_number:
        candidate_numbers.append(legacy_ticket_number)

    placeholders = ", ".join("?" for _ in candidate_numbers)
    return connection.execute(
        f"SELECT id, ticket_number FROM repair_tickets WHERE ticket_number IN ({placeholders}) ORDER BY id ASC LIMIT 1",
        tuple(candidate_numbers),
    ).fetchone()


def _upsert_tickets(connection: sqlite3.Connection, customer_ids: dict[tuple[str, str], int]) -> dict[str, int]:
    ticket_ids: dict[str, int] = {}
    current_timestamp = "2026-06-15T12:00:00+00:00"
    
    # Terminal statuses that mark completion
    TERMINAL_STATUSES = {"Picked Up / Closed", "Not Repairable", "Returned Unrepaired", "Customer Declined"}
    
    for customer in REAL_SEED_CUSTOMERS:
        customer_key = (customer["full_name"], _normalize_phone(customer["phone"]))
        customer_id = customer_ids[customer_key]
        for ticket in customer["jobs"]:
            # Calculate completed_at from status_history if ticket reached a terminal status
            completed_at = None
            if ticket["status"] in TERMINAL_STATUSES:
                for old_status, new_status, changed_by, note, created_at in ticket["status_history"]:
                    if new_status in TERMINAL_STATUSES:
                        completed_at = created_at
                        break
            
            existing = _find_existing_seed_ticket(connection, ticket)
            if existing is None:
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
                        updated_at,
                        completed_at
                    ) VALUES (?, ?, NULL, ?, NULL, NULL, NULL, NULL, NULL, ?, ?, ?, 'unknown', 'unknown', 'unknown', 'unknown', NULL, 0, 0, ?, ?, ?, 0, ?, 'normal', 'Mattis', 'Mattis', ?, ?, ?, ?)
                    """,
                    (
                        ticket["ticket_number"],
                        customer_id,
                        ticket["device"],
                        ticket["issue_category"],
                        ticket["issue_description"],
                        ticket["condition_summary"],
                        ticket["estimated_price"],
                        ticket["final_price"],
                        ticket["payment_status"],
                        ticket["status"],
                        ticket["intake_date"],
                        current_timestamp,
                        current_timestamp,
                        completed_at,
                    ),
                )
                ticket_id = int(cursor.lastrowid)
            else:
                ticket_id = int(existing["id"])
                _delete_ticket_related_rows(connection, ticket_id)
                connection.execute(
                    """
                    UPDATE repair_tickets
                    SET ticket_number = ?,
                        customer_id = ?,
                        device_model_id = NULL,
                        device_model_text_override = ?,
                        carrier = NULL,
                        sim_type = NULL,
                        imei_serial = NULL,
                        device_color = NULL,
                        filter_status = NULL,
                        issue_category = ?,
                        issue_description = ?,
                        condition_summary = ?,
                        water_damage_status = 'unknown',
                        dropped_status = 'unknown',
                        powers_on_status = 'unknown',
                        charges_status = 'unknown',
                        customer_approval_limit = NULL,
                        must_call_before_repair = 0,
                        customer_prefers_replacement_if_high = 0,
                        estimated_price = ?,
                        final_price = ?,
                        payment_status = ?,
                        diagnostic_fee = 0,
                        status = ?,
                        priority = 'normal',
                        intake_staff = 'Mattis',
                        assigned_technician = 'Mattis',
                        intake_date = ?,
                        updated_at = ?,
                        completed_at = ?
                    WHERE id = ?
                    """,
                    (
                        ticket["ticket_number"],
                        customer_id,
                        ticket["device"],
                        ticket["issue_category"],
                        ticket["issue_description"],
                        ticket["condition_summary"],
                        ticket["estimated_price"],
                        ticket["final_price"],
                        ticket["payment_status"],
                        ticket["status"],
                        ticket["intake_date"],
                        current_timestamp,
                        completed_at,
                        ticket_id,
                    ),
                )

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

            ticket_ids[ticket["ticket_number"]] = ticket_id
            if ticket.get("legacy_ticket_number"):
                ticket_ids[ticket["legacy_ticket_number"]] = ticket_id

    return ticket_ids


def sync_real_customer_job_data(connection: sqlite3.Connection, *, replace_existing: bool = False) -> dict[str, int]:
    if replace_existing:
        wipe_real_customer_job_data(connection)
    customer_ids = _upsert_customers(connection)
    return _upsert_tickets(connection, customer_ids)
