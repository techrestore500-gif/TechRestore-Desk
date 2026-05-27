"""Repository for loaner phone and checkout data access."""
from __future__ import annotations
from app.database import (
    ensure_customer_exists,
    checkout_loaner,
    create_loaner_phone,
    get_ticket,
    get_loaner_phone,
    list_loaner_phones,
    list_overdue_loaner_checkouts,
    return_loaner as db_return_loaner,
    update_loaner_phone,
)


class LoanerRepository:
    """Handles all database operations for loaners."""

    @staticmethod
    def list(status: str | None = None) -> list[dict]:
        return list_loaner_phones(status=status)

    @staticmethod
    def create(payload: dict) -> dict:
        return create_loaner_phone(payload)

    @staticmethod
    def get(loaner_id: int) -> dict | None:
        return get_loaner_phone(loaner_id)

    @staticmethod
    def update(loaner_id: int, payload: dict) -> dict | None:
        return update_loaner_phone(loaner_id, payload)

    @staticmethod
    def checkout(loaner_id: int, payload: dict) -> dict | None:
        return checkout_loaner(loaner_id, payload)

    @staticmethod
    def customer_exists(customer_id: int) -> bool:
        return ensure_customer_exists(customer_id)

    @staticmethod
    def ticket_exists(ticket_id: int) -> bool:
        return get_ticket(ticket_id) is not None

    @staticmethod
    def return_loaner(loaner_id: int, payload: dict) -> dict:
        return db_return_loaner(loaner_id, payload)

    @staticmethod
    def list_overdue() -> list[dict]:
        return list_overdue_loaner_checkouts()
