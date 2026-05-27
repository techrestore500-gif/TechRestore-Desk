from fastapi import APIRouter

from app.models import DashboardAlertsResponse, DashboardSummaryResponse
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_summary() -> DashboardSummaryResponse:
    return DashboardSummaryResponse.model_validate(DashboardService.get_summary())

@router.get("/alerts", response_model=DashboardAlertsResponse)
def get_alerts() -> DashboardAlertsResponse:
    return DashboardService.get_alerts()