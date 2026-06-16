"""Repository for ticket data access operations."""
from __future__ import annotations
import sqlite3
from datetime import UTC, datetime
from typing import Optional

from app.database import get_connection, utc_now, build_device_label, row_to_dict


class TicketRepository:
    """Handles all database operations for tickets."""

    @staticmethod
    def generate_ticket_number(connection: sqlite3.Connection) -> str:
        """Generate the next ticket number."""
        count = connection.execute(
            "SELECT COUNT(*) AS count FROM repair_tickets"
        ).fetchone()["count"]
        return f"TR-{count + 1:05d}"

    @staticmethod
    def create(payload: dict) -> dict:
        """Create a new ticket."""
        timestamp = utc_now()
        with get_connection() as connection:
            ticket_number = TicketRepository.generate_ticket_number(connection)
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
        return TicketRepository.get(ticket_id)

    @staticmethod
    def list(status: str | None = None, search: str | None = None) -> list[dict]:
        """List tickets with optional filtering."""
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

    @staticmethod
    def list_paginated(
        *,
        page: int = 1,
        page_size: int = 50,
        status: str | None = None,
        search: str | None = None,
    ) -> dict:
        page = max(1, page)
        page_size = max(1, min(500, page_size))
        offset = (page - 1) * page_size

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
            total_row = connection.execute(
                f"""
                SELECT COUNT(*) AS count
                FROM repair_tickets
                INNER JOIN customers ON customers.id = repair_tickets.customer_id
                LEFT JOIN supported_device_models ON supported_device_models.id = repair_tickets.device_model_id
                {where_clause}
                """,
                tuple(parameters),
            ).fetchone()

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
                LIMIT ? OFFSET ?
                """,
                tuple(parameters + [page_size, offset]),
            ).fetchall()

        items: list[dict] = []
        for row in rows:
            item = dict(row)
            item["device_label"] = build_device_label(row)
            items.append(item)

        total = int(total_row["count"]) if total_row else 0
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    def get(ticket_id: int) -> dict | None:
        """Get a ticket by ID with all related data."""
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
        item["history"] = TicketRepository._list_history_with_connection(connection, ticket_id)
        item["notes"] = TicketRepository._list_notes_with_connection(connection, ticket_id)
        item["repair_actions"] = TicketRepository._list_repair_actions_with_connection(connection, ticket_id)
        return item

    @staticmethod
    def _list_history_with_connection(connection: sqlite3.Connection, ticket_id: int) -> list[dict]:
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

    @staticmethod
    def _list_notes_with_connection(connection: sqlite3.Connection, ticket_id: int) -> list[dict]:
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

    @staticmethod
    def _list_repair_actions_with_connection(connection: sqlite3.Connection, ticket_id: int) -> list[dict]:
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

    @staticmethod
    def get_loaner_agreement(ticket_id: int) -> dict | None:
        """Get the most recent loaner checkout enriched for printing."""
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    loaner_checkouts.id,
                    loaner_checkouts.ticket_id,
                    repair_tickets.ticket_number,
                    repair_tickets.customer_id,
                    customers.full_name AS customer_name,
                    COALESCE(customers.primary_phone, customers.alternate_phone) AS customer_phone,
                    repair_tickets.issue_category,
                    repair_tickets.device_model_id,
                    repair_tickets.device_model_text_override,
                    supported_device_models.manufacturer,
                    supported_device_models.model_name,
                    loaner_checkouts.loaner_phone_id,
                    loaner_phones.loaner_code,
                    loaner_phones.manufacturer AS loaner_manufacturer,
                    loaner_phones.model AS loaner_model,
                    loaner_checkouts.date_out,
                    loaner_checkouts.expected_return_date,
                    loaner_checkouts.condition_out,
                    loaner_checkouts.charger_included,
                    loaner_checkouts.sim_moved,
                    loaner_checkouts.outgoing_call_tested,
                    loaner_checkouts.incoming_call_tested,
                    loaner_checkouts.deposit_amount,
                    loaner_checkouts.agreement_signed,
                    loaner_checkouts.checkout_staff,
                    loaner_checkouts.status
                FROM loaner_checkouts
                INNER JOIN repair_tickets ON repair_tickets.id = loaner_checkouts.ticket_id
                INNER JOIN customers ON customers.id = repair_tickets.customer_id
                INNER JOIN loaner_phones ON loaner_phones.id = loaner_checkouts.loaner_phone_id
                LEFT JOIN supported_device_models ON supported_device_models.id = repair_tickets.device_model_id
                WHERE loaner_checkouts.ticket_id = ?
                ORDER BY loaner_checkouts.id DESC
                LIMIT 1
                """,
                (ticket_id,),
            ).fetchone()

        if row is None:
            return None

        item = dict(row)
        item["device_label"] = build_device_label(row)
        item["loaner_device_label"] = " ".join(
            part for part in [row["loaner_manufacturer"], row["loaner_model"]] if part
        )
        item["charger_included"] = bool(item["charger_included"])
        item["sim_moved"] = bool(item["sim_moved"])
        item["outgoing_call_tested"] = bool(item["outgoing_call_tested"])
        item["incoming_call_tested"] = bool(item["incoming_call_tested"])
        item["agreement_signed"] = bool(item["agreement_signed"])
        item.pop("device_model_id", None)
        item.pop("device_model_text_override", None)
        item.pop("manufacturer", None)
        item.pop("model_name", None)
        item.pop("loaner_manufacturer", None)
        item.pop("loaner_model", None)
        return item

    @staticmethod
    def update(ticket_id: int, payload: dict) -> dict | None:
        """Update a ticket."""
        existing_ticket = TicketRepository.get(ticket_id)
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
        return TicketRepository.get(ticket_id)

    @staticmethod
    def add_status_history(ticket_id: int, payload: dict) -> dict:
        """Add a status history entry, update ticket status, and optionally set final_price."""
        existing_ticket = TicketRepository.get(ticket_id)
        previous_status = existing_ticket["status"]
        timestamp = utc_now()
        final_price = payload.get("final_price")
        new_status = payload["new_status"]
        
        # Terminal statuses that mark completion
        TERMINAL_STATUSES = {"Picked Up / Closed", "Not Repairable", "Returned Unrepaired", "Customer Declined"}
        completed_at = timestamp if new_status in TERMINAL_STATUSES else None

        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO ticket_status_history (ticket_id, old_status, new_status, changed_by, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket_id,
                    previous_status,
                    new_status,
                    payload.get("changed_by"),
                    payload.get("note"),
                    timestamp,
                ),
            )
            if final_price is not None:
                if completed_at is not None:
                    connection.execute(
                        "UPDATE repair_tickets SET status = ?, final_price = ?, updated_at = ?, completed_at = ? WHERE id = ?",
                        (new_status, final_price, timestamp, completed_at, ticket_id),
                    )
                else:
                    connection.execute(
                        "UPDATE repair_tickets SET status = ?, final_price = ?, updated_at = ? WHERE id = ?",
                        (new_status, final_price, timestamp, ticket_id),
                    )
            else:
                if completed_at is not None:
                    connection.execute(
                        "UPDATE repair_tickets SET status = ?, updated_at = ?, completed_at = ? WHERE id = ?",
                        (new_status, timestamp, completed_at, ticket_id),
                    )
                else:
                    connection.execute(
                        "UPDATE repair_tickets SET status = ?, updated_at = ? WHERE id = ?",
                        (new_status, timestamp, ticket_id),
                    )
            connection.commit()
        return TicketRepository.list_history(ticket_id)[-1]

    @staticmethod
    def list_history(ticket_id: int) -> list[dict]:
        """List status history for a ticket."""
        with get_connection() as connection:
            return TicketRepository._list_history_with_connection(connection, ticket_id)

    @staticmethod
    def add_note(ticket_id: int, payload: dict) -> dict:
        """Add a note to a ticket."""
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

            row = connection.execute(
                "SELECT id, ticket_id, note_type, body, created_by, created_at FROM ticket_notes WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        return dict(row)

    @staticmethod
    def list_notes(ticket_id: int) -> list[dict]:
        """List notes for a ticket."""
        with get_connection() as connection:
            return TicketRepository._list_notes_with_connection(connection, ticket_id)

    @staticmethod
    def list_repair_actions(ticket_id: int) -> list[dict]:
        """List repair actions for a ticket."""
        with get_connection() as connection:
            return TicketRepository._list_repair_actions_with_connection(connection, ticket_id)

    @staticmethod
    def add_repair_action(ticket_id: int, payload: dict) -> dict:
        """Add a repair action to a ticket."""
        from app.database import calculate_pricing
        
        if TicketRepository.get(ticket_id) is None:
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

    @staticmethod
    def has_active_loaner_checkout(ticket_id: int) -> bool:
        """Check whether a ticket still has an active loaner checkout."""
        from app.database import has_active_loaner_checkout_for_ticket

        return has_active_loaner_checkout_for_ticket(ticket_id)

    @staticmethod
    def close_ticket(
        ticket_id: int,
        *,
        old_status: str,
        final_price: float | None,
        changed_by: str | None,
        close_note: str,
    ) -> None:
        """Persist ticket close state and append status history."""
        # Gate 1 migration note: repository method only performs writes passed from service.
        # Business rule decisions (guardrails/defaulting) are intentionally handled in service.
        timestamp = utc_now()
        with get_connection() as connection:
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
                (ticket_id, old_status, changed_by, close_note, timestamp),
            )
            connection.commit()

    @staticmethod
    def close_with_guard(ticket_id: int, payload: dict) -> dict | None:
        """Close a ticket with validation.

        Legacy compatibility wrapper retained during incremental migration.
        New call sites should use service-level close orchestration.
        """
        existing_ticket = TicketRepository.get(ticket_id)
        if existing_ticket is None:
            return None
        if TicketRepository.has_active_loaner_checkout(ticket_id):
            raise ValueError("Cannot close ticket while loaner is still checked out")

        close_note = payload.get("note") or "Ticket closed"
        changed_by = payload.get("changed_by")
        final_price = payload.get("final_price", existing_ticket.get("final_price"))

        TicketRepository.close_ticket(
            ticket_id,
            old_status=existing_ticket["status"],
            final_price=final_price,
            changed_by=changed_by,
            close_note=close_note,
        )

        return {
            "ticket_id": ticket_id,
            "status": "Picked Up / Closed",
            "closed": True,
        }
