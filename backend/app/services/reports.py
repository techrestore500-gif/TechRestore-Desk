"""Service layer for business reporting."""
from app.models import ReportSummaryResponse
from app.repositories.reports import ReportsRepository


class ReportsService:
    """Business logic for reporting endpoints."""

    @staticmethod
    def get_summary(
        start_date: str | None = None,
        end_date: str | None = None,
        technician: str | None = None,
        repair_category: str | None = None,
    ) -> ReportSummaryResponse:
        return ReportSummaryResponse.model_validate(
            ReportsRepository.summary(
                start_date=start_date,
                end_date=end_date,
                technician=technician,
                repair_category=repair_category,
            )
        )
