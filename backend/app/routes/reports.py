from fastapi import APIRouter, Depends

from app.auth.dependencies import require_role
from app.models import ReportSummaryResponse
from app.services.reports import ReportsService

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/summary", response_model=ReportSummaryResponse)
def get_report_summary(
    start_date: str | None = None,
    end_date: str | None = None,
    technician: str | None = None,
    repair_category: str | None = None,
    _: dict = Depends(require_role("owner", "admin", "manager", "front_desk", "technician", "viewer")),
) -> ReportSummaryResponse:
    return ReportsService.get_summary(
        start_date=start_date,
        end_date=end_date,
        technician=technician,
        repair_category=repair_category,
    )
