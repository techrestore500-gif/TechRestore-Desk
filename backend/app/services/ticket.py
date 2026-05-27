"""Service layer for ticket business logic."""
from app.events.audit_events import ticket_closed, ticket_status_changed
from app.events.dispatcher import event_dispatcher
from app.events.types import TicketClosedEvent, TicketCreatedEvent
from app.repositories.ticket import TicketRepository
from app.database import (
    ensure_customer_exists,
    ensure_supported_model_exists,
    get_status_workflow_rules,
    has_active_loaner_checkout_for_ticket,
)
from app.services.audit import AuditService


CLOSED_STATUSES = {"Picked Up / Closed", "Not Repairable", "Returned Unrepaired", "Customer Declined"}
NO_PRICE_REQUIRED = {"Returned Unrepaired", "Not Repairable", "Customer Declined"}


class TicketService:
    """Business logic for ticket operations."""

    @staticmethod
    def create_ticket(payload: dict) -> dict:
        """Create a new ticket with validation."""
        # Validate customer exists
        if not ensure_customer_exists(payload["customer_id"]):
            raise ValueError("Customer does not exist")
        
        # Validate device model if provided
        if payload.get("device_model_id") and not ensure_supported_model_exists(payload["device_model_id"]):
            raise ValueError("Supported model does not exist")
        
        created = TicketRepository.create(payload)
        AuditService.log(
            entity_type="ticket",
            entity_id=created["id"],
            action="ticket_created",
            new_value={
                "ticket_number": created.get("ticket_number"),
                "customer_id": created.get("customer_id"),
                "status": created.get("status"),
            },
        )
        event_dispatcher.publish(TicketCreatedEvent(ticket_id=created["id"], customer_id=created["customer_id"]))
        return created

    @staticmethod
    def list_tickets(status: str | None = None, search: str | None = None) -> list[dict]:
        """List tickets with optional filtering."""
        return TicketRepository.list(status=status, search=search)

    @staticmethod
    def list_tickets_paginated(
        *,
        page: int = 1,
        page_size: int = 50,
        status: str | None = None,
        search: str | None = None,
    ) -> dict:
        return TicketRepository.list_paginated(
            page=page,
            page_size=page_size,
            status=status,
            search=search,
        )

    @staticmethod
    def get_ticket(ticket_id: int) -> dict | None:
        """Get a ticket by ID."""
        return TicketRepository.get(ticket_id)

    @staticmethod
    def get_ticket_loaner_agreement(ticket_id: int) -> dict | None:
        """Get the most recent loaner agreement payload for a ticket."""
        return TicketRepository.get_loaner_agreement(ticket_id)

    @staticmethod
    def update_ticket(ticket_id: int, payload: dict) -> dict | None:
        """Update a ticket with validation."""
        # Validate device model if being updated
        if payload.get("device_model_id") and not ensure_supported_model_exists(payload["device_model_id"]):
            raise ValueError("Supported model does not exist")
        
        return TicketRepository.update(ticket_id, payload)

    @staticmethod
    def update_ticket_status(ticket_id: int, payload: dict) -> dict:
        """Update ticket status with history tracking and business-rule validation."""
        ticket = TicketRepository.get(ticket_id)
        if ticket is None:
            raise LookupError("Ticket not found")

        rules = get_status_workflow_rules()
        transitions: dict[str, list[str]] = rules.get("transitions", {})
        guardrails: dict[str, bool] = rules.get("guardrails", {})

        current_status: str = ticket["status"]
        new_status: str = payload["new_status"]

        # ── 1. Target status must be a known status ──────────────────────────
        all_statuses = set(transitions.keys())
        if new_status not in all_statuses:
            raise ValueError(f"Unknown status: '{new_status}'")

        # ── 2. Transition must be allowed from the current status ────────────
        allowed = set(transitions.get(current_status, []))
        if new_status not in allowed:
            raise ValueError(
                f"Cannot move from '{current_status}' to '{new_status}'. "
                f"Allowed next statuses: {sorted(allowed) or ['none — this is a terminal status']}"
            )

        # ── 3. Guardrails ────────────────────────────────────────────────────
        # Closing / Ready-for-Pickup: no active loaner
        enforce_ready_no_loaner = bool(guardrails.get("enforce_no_active_loaner_for_ready_for_pickup", True))
        enforce_closed_no_loaner = bool(guardrails.get("enforce_no_active_loaner_for_closed_statuses", True))
        if (enforce_closed_no_loaner and new_status in CLOSED_STATUSES) or (
            enforce_ready_no_loaner and new_status == "Ready for Pickup"
        ):
            if has_active_loaner_checkout_for_ticket(ticket_id):
                raise ValueError(
                    "Cannot advance ticket while a loaner phone is still checked out. "
                    "Return the loaner first."
                )

        # Ready for Pickup / closing (except no-charge cases): final price required
        enforce_ready_price = bool(guardrails.get("enforce_final_price_for_ready_for_pickup", True))
        enforce_closed_price = bool(guardrails.get("enforce_final_price_for_closed_paid_statuses", True))
        require_price_for = set()
        if enforce_ready_price:
            require_price_for.add("Ready for Pickup")
        if enforce_closed_price:
            require_price_for |= CLOSED_STATUSES - NO_PRICE_REQUIRED
        if new_status in require_price_for:
            if ticket.get("final_price") is None and payload.get("final_price") is None:
                raise ValueError(
                    f"A final price must be set before marking the ticket '{new_status}'."
                )

        history_item = TicketRepository.add_status_history(ticket_id, payload)
        AuditService.log_event(
            ticket_status_changed(
                ticket_id=ticket_id,
                old_status=current_status,
                new_status=new_status,
                note=payload.get("note"),
            )
        )
        return history_item

    @staticmethod
    def add_ticket_note(ticket_id: int, payload: dict) -> dict:
        """Add a note to a ticket."""
        ticket = TicketRepository.get(ticket_id)
        if ticket is None:
            raise ValueError("Ticket not found")
        
        return TicketRepository.add_note(ticket_id, payload)

    @staticmethod
    def get_ticket_history(ticket_id: int) -> list[dict]:
        """Get status history for a ticket."""
        ticket = TicketRepository.get(ticket_id)
        if ticket is None:
            raise ValueError("Ticket not found")
        
        return TicketRepository.list_history(ticket_id)

    @staticmethod
    def get_ticket_notes(ticket_id: int) -> list[dict]:
        """Get notes for a ticket."""
        ticket = TicketRepository.get(ticket_id)
        if ticket is None:
            raise ValueError("Ticket not found")
        
        return TicketRepository.list_notes(ticket_id)

    @staticmethod
    def add_repair_action(ticket_id: int, payload: dict) -> dict:
        """Add a repair action to a ticket."""
        return TicketRepository.add_repair_action(ticket_id, payload)

    @staticmethod
    def get_repair_actions(ticket_id: int) -> list[dict]:
        """Get repair actions for a ticket."""
        ticket = TicketRepository.get(ticket_id)
        if ticket is None:
            raise ValueError("Ticket not found")
        
        return TicketRepository.list_repair_actions(ticket_id)

    @staticmethod
    def close_ticket(ticket_id: int, payload: dict) -> dict | None:
        """Close a ticket with workflow validation and status history."""
        # Gate 1 migration note: service owns business orchestration so routes remain HTTP-only
        # and repositories stay persistence-focused.
        ticket = TicketRepository.get(ticket_id)
        if ticket is None:
            return None

        if TicketRepository.has_active_loaner_checkout(ticket_id):
            raise ValueError("Cannot close ticket while loaner is still checked out")

        close_note = payload.get("note") or "Ticket closed"
        changed_by = payload.get("changed_by")
        final_price = payload.get("final_price", ticket.get("final_price"))

        TicketRepository.close_ticket(
            ticket_id,
            old_status=ticket["status"],
            final_price=final_price,
            changed_by=changed_by,
            close_note=close_note,
        )

        AuditService.log_event(
            ticket_closed(
                ticket_id=ticket_id,
                old_status=ticket["status"],
                final_price=final_price,
                note=close_note,
            )
        )
        event_dispatcher.publish(TicketClosedEvent(ticket_id=ticket_id, final_price=final_price))

        return {
            "ticket_id": ticket_id,
            "status": "Picked Up / Closed",
            "closed": True,
        }
