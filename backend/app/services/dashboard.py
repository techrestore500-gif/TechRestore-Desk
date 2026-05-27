"""Service layer for dashboard aggregation."""
from app.core.cache import ttl_cache
from app.models import DashboardAlertsResponse, DashboardSummaryResponse, LoanerAlertSummary, LoanerCheckoutResponse
from app.repositories.dashboard import DashboardRepository


_DASHBOARD_SUMMARY_TTL_SECONDS = 10
_DASHBOARD_ALERTS_TTL_SECONDS = 5


class DashboardService:
    """Business logic for dashboard summary and alerts."""

    @staticmethod
    def get_summary() -> dict:
        cache_key = "dashboard:summary"
        cached = ttl_cache.get(cache_key)
        if cached is not None:
            return cached
        summary = DashboardRepository.summary()
        ttl_cache.set(cache_key, summary, _DASHBOARD_SUMMARY_TTL_SECONDS)
        return summary

    @staticmethod
    def get_alerts() -> DashboardAlertsResponse:
        cache_key = "dashboard:alerts"
        cached = ttl_cache.get(cache_key)
        if cached is not None:
            return DashboardAlertsResponse.model_validate(cached)

        summary = LoanerAlertSummary.model_validate(DashboardRepository.loaner_alert_summary())
        overdue_items = [LoanerCheckoutResponse.model_validate(item) for item in DashboardRepository.overdue_loaners()]
        response = DashboardAlertsResponse(summary=summary, overdue_items=overdue_items)
        ttl_cache.set(cache_key, response.model_dump(), _DASHBOARD_ALERTS_TTL_SECONDS)
        return response
