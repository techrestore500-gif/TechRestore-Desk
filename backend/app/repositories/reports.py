"""Repository for reporting aggregate queries."""
from app.database import get_report_summary


class ReportsRepository:
    """Handles reporting data access."""

    @staticmethod
    def summary(
        start_date: str | None = None,
        end_date: str | None = None,
        technician: str | None = None,
        repair_category: str | None = None,
    ) -> dict:
        return get_report_summary(
            start_date=start_date,
            end_date=end_date,
            technician=technician,
            repair_category=repair_category,
        )
