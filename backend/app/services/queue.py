"""Service layer for technician queue presentation."""
from app.events.audit_events import technician_assignment_changed
from app.repositories.queue import QueueRepository
from app.services.audit import AuditService


class QueueService:
    """Business logic for technician queue queries."""

    @staticmethod
    def get_queue() -> dict[str, list[dict]]:
        return QueueRepository.get_queue()

    @staticmethod
    def assign_ticket(ticket_id: int, assigned_technician: str | None) -> dict | None:
        # Gate 1 migration note: workflow validation and normalization stay in service.
        try:
            previous_assignment = QueueRepository.get_assignment(ticket_id)
        except Exception:
            previous_assignment = None
        normalized = assigned_technician.strip() if isinstance(assigned_technician, str) else None
        if normalized == "":
            normalized = None
        result = QueueRepository.assign_ticket(ticket_id=ticket_id, assigned_technician=normalized)
        if result is None:
            return None

        AuditService.log_event(
            technician_assignment_changed(
                ticket_id=ticket_id,
                old_value=previous_assignment,
                new_value=normalized,
            )
        )
        return result
