from fastapi import APIRouter

from app.models import HealthResponse
from app.services.health import HealthService


router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse.model_validate(HealthService.get_health_status())