"""Service layer for technician hours business logic."""
from app.database import get_ticket
from app.repositories.hours import HoursRepository


class HoursService:
    """Business logic for hours logging and reporting."""

    @staticmethod
    def create_hours(payload: dict) -> dict:
        ticket_id = payload.get("ticket_id")
        if ticket_id and get_ticket(ticket_id) is None:
            raise ValueError(f"Ticket {ticket_id} not found")
        return HoursRepository.create(payload)

    @staticmethod
    def get_active_session(technician: str) -> dict | None:
        return HoursRepository.get_active_session(technician.strip())

    @staticmethod
    def clock_in(payload: dict) -> dict:
        technician = payload["technician"].strip()
        if not technician:
            raise ValueError("Technician name is required")
        ticket_id = payload.get("ticket_id")
        if ticket_id and get_ticket(ticket_id) is None:
            raise ValueError(f"Ticket {ticket_id} not found")
        return HoursRepository.clock_in({**payload, "technician": technician})

    @staticmethod
    def clock_out(payload: dict) -> dict:
        technician = payload["technician"].strip()
        if not technician:
            raise ValueError("Technician name is required")
        ticket_id = payload.get("ticket_id")
        if ticket_id and get_ticket(ticket_id) is None:
            raise ValueError(f"Ticket {ticket_id} not found")
        return HoursRepository.clock_out({**payload, "technician": technician})

    @staticmethod
    def list_hours(start_date: str | None = None, end_date: str | None = None, technician: str | None = None) -> list[dict]:
        return HoursRepository.list(start_date=start_date, end_date=end_date, technician=technician)

    @staticmethod
    def get_summary(start_date: str | None = None, end_date: str | None = None, technician: str | None = None) -> dict:
        return HoursRepository.summary(start_date=start_date, end_date=end_date, technician=technician)
