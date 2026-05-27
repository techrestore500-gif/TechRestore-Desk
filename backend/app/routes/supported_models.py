from fastapi import APIRouter

from app.models import SupportedModelResponse
from app.services.supported_models import SupportedModelService


router = APIRouter(prefix="/api/supported-models", tags=["supported-models"])


@router.get("", response_model=list[SupportedModelResponse])
def get_supported_models() -> list[SupportedModelResponse]:
    models = SupportedModelService.list_models()
    return [SupportedModelResponse.model_validate(item) for item in models]