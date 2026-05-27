"""Repository for technician hours data access."""
from app.database import (
    clock_in_technician,
    clock_out_technician,
    get_active_clock_session,
    get_hours_entry,
    get_hours_summary,
    list_hours,
    log_hours,
)


class HoursRepository:
    """Handles database operations for technician hours."""

    @staticmethod
    def create(payload: dict) -> dict:
        return log_hours(payload)

    @staticmethod
    def get(hours_id: int) -> dict | None:
        return get_hours_entry(hours_id)

    @staticmethod
    def get_active_session(technician: str) -> dict | None:
        return get_active_clock_session(technician)

    @staticmethod
    def clock_in(payload: dict) -> dict:
        return clock_in_technician(payload)

    @staticmethod
    def clock_out(payload: dict) -> dict:
        return clock_out_technician(payload)

    @staticmethod
    def list(start_date: str | None = None, end_date: str | None = None, technician: str | None = None) -> list[dict]:
        return list_hours(start_date=start_date, end_date=end_date, technician=technician)

    @staticmethod
    def summary(start_date: str | None = None, end_date: str | None = None, technician: str | None = None) -> dict:
        return get_hours_summary(start_date=start_date, end_date=end_date, technician=technician)
