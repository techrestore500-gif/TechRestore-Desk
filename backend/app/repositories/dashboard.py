"""Repository for dashboard aggregate queries."""
from app.database import get_dashboard_summary, get_loaner_alert_summary, list_overdue_loaner_checkouts


class DashboardRepository:
    """Handles dashboard-related data access."""

    @staticmethod
    def summary() -> dict:
        return get_dashboard_summary()

    @staticmethod
    def loaner_alert_summary() -> dict:
        return get_loaner_alert_summary()

    @staticmethod
    def overdue_loaners() -> list[dict]:
        return list_overdue_loaner_checkouts()
