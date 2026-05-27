"""Service layer for loaner business logic."""
from app.events.audit_events import loaner_activity
from app.events.dispatcher import event_dispatcher
from app.events.types import LoanerOverdueEvent
from app.repositories.loaner import LoanerRepository
from app.services.audit import AuditService


class LoanerService:
    """Business logic for loaner operations."""

    @staticmethod
    def list_loaners(status: str | None = None) -> list[dict]:
        return LoanerRepository.list(status=status)

    @staticmethod
    def create_loaner(payload: dict) -> dict:
        return LoanerRepository.create(payload)

    @staticmethod
    def get_loaner(loaner_id: int) -> dict | None:
        return LoanerRepository.get(loaner_id)

    @staticmethod
    def update_loaner(loaner_id: int, payload: dict) -> dict | None:
        return LoanerRepository.update(loaner_id, payload)

    @staticmethod
    def checkout_loaner(loaner_id: int, payload: dict) -> dict | None:
        # Gate 1 migration note: service coordinates workflow rules while repository owns data access.
        before = LoanerRepository.get(loaner_id)
        if not LoanerRepository.customer_exists(payload["customer_id"]):
            raise ValueError("Customer does not exist")
        if not LoanerRepository.ticket_exists(payload["ticket_id"]):
            raise ValueError("Ticket does not exist")
        checkout = LoanerRepository.checkout(loaner_id, payload)
        if checkout is not None:
            AuditService.log_event(
                loaner_activity(
                    loaner_id=loaner_id,
                    action="loaner_checked_out",
                    old_value=before,
                    new_value=checkout,
                )
            )
        return checkout

    @staticmethod
    def return_loaner(loaner_id: int, payload: dict) -> dict:
        before = LoanerRepository.get(loaner_id)
        if before is None:
            raise ValueError("Loaner not found")
        checkout = LoanerRepository.return_loaner(loaner_id, payload)
        AuditService.log_event(
            loaner_activity(
                loaner_id=loaner_id,
                action="loaner_returned",
                old_value=before,
                new_value=checkout,
            )
        )
        return checkout

    @staticmethod
    def list_overdue_loaners() -> list[dict]:
        overdue = LoanerRepository.list_overdue()
        for item in overdue:
            event_dispatcher.publish(
                LoanerOverdueEvent(
                    checkout_id=item["id"],
                    loaner_phone_id=item["loaner_phone_id"],
                    ticket_id=item["ticket_id"],
                )
            )
        return overdue
