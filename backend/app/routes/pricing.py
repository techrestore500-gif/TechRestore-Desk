from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_role
from app.models import PricingCalculateRequest, PricingCalculationResponse, PricingDefaultsUpdate
from app.services.pricing import PricingService


router = APIRouter(prefix="/api/pricing", tags=["pricing"])


@router.post("/calculate", response_model=PricingCalculationResponse)
def post_calculate_pricing(payload: PricingCalculateRequest) -> PricingCalculationResponse:
    return PricingCalculationResponse.model_validate(PricingService.calculate(payload.model_dump(exclude_none=True)))


@router.get("/rules")
def get_pricing_rules() -> dict:
    return PricingService.get_rules()


@router.patch("/rules")
def patch_pricing_rules(
    payload: PricingDefaultsUpdate,
    _: dict = Depends(require_role("admin", "front_desk")),
) -> dict:
    try:
        return {"defaults": PricingService.update_rules(payload.model_dump(exclude_none=True))}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
