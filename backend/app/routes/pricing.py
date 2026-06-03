from fastapi import APIRouter, Depends, HTTPException

from app import database
from app.auth.dependencies import require_role
from app.models import (
    PricingBrandCreate,
    PricingBrandResponse,
    PricingBrandUpdate,
    PricingCalculateRequest,
    PricingCalculationResponse,
    PricingCatalogResponse,
    PricingDefaultsUpdate,
    PricingIssueTypeCreate,
    PricingIssueTypeResponse,
    PricingIssueTypeUpdate,
    PricingModelCreate,
    PricingModelResponse,
    PricingModelUpdate,
    PricingRepairTypeCreate,
    PricingRepairTypeResponse,
    PricingRepairTypeUpdate,
    PricingRuleCreate,
    PricingRuleResponse,
    PricingRuleSuggestionResponse,
    PricingRuleUpdate,
)
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


@router.get("/catalog", response_model=PricingCatalogResponse)
def get_pricing_catalog(include_inactive: bool = True) -> PricingCatalogResponse:
    return PricingCatalogResponse(
        brands=database.list_pricing_brands(include_inactive=include_inactive),
        models=database.list_pricing_models(include_inactive=include_inactive),
        issue_types=database.list_pricing_issue_types(include_inactive=include_inactive),
        repair_types=database.list_pricing_repair_types(include_inactive=include_inactive),
        rules=database.list_pricing_rules({"include_inactive": include_inactive}),
    )


@router.get("/catalog/brands", response_model=list[PricingBrandResponse])
def get_pricing_brands(include_inactive: bool = True) -> list[PricingBrandResponse]:
    return database.list_pricing_brands(include_inactive=include_inactive)


@router.post("/catalog/brands", response_model=PricingBrandResponse, status_code=201)
def post_pricing_brand(
    payload: PricingBrandCreate,
    _: dict = Depends(require_role("admin", "front_desk")),
) -> PricingBrandResponse:
    try:
        return PricingBrandResponse.model_validate(database.create_pricing_brand(payload.model_dump()))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.patch("/catalog/brands/{brand_id}", response_model=PricingBrandResponse)
def patch_pricing_brand(
    brand_id: int,
    payload: PricingBrandUpdate,
    _: dict = Depends(require_role("admin", "front_desk")),
) -> PricingBrandResponse:
    try:
        updated = database.update_pricing_brand(brand_id, payload.model_dump(exclude_none=True))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if updated is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    return PricingBrandResponse.model_validate(updated)


@router.get("/catalog/models", response_model=list[PricingModelResponse])
def get_pricing_models(brand_id: int | None = None, include_inactive: bool = True) -> list[PricingModelResponse]:
    return database.list_pricing_models(brand_id=brand_id, include_inactive=include_inactive)


@router.post("/catalog/models", response_model=PricingModelResponse, status_code=201)
def post_pricing_model(
    payload: PricingModelCreate,
    _: dict = Depends(require_role("admin", "front_desk")),
) -> PricingModelResponse:
    try:
        return PricingModelResponse.model_validate(database.create_pricing_model(payload.model_dump()))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.patch("/catalog/models/{model_id}", response_model=PricingModelResponse)
def patch_pricing_model(
    model_id: int,
    payload: PricingModelUpdate,
    _: dict = Depends(require_role("admin", "front_desk")),
) -> PricingModelResponse:
    try:
        updated = database.update_pricing_model(model_id, payload.model_dump(exclude_none=True))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if updated is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return PricingModelResponse.model_validate(updated)


@router.get("/catalog/issue-types", response_model=list[PricingIssueTypeResponse])
def get_pricing_issue_types(include_inactive: bool = True) -> list[PricingIssueTypeResponse]:
    return database.list_pricing_issue_types(include_inactive=include_inactive)


@router.post("/catalog/issue-types", response_model=PricingIssueTypeResponse, status_code=201)
def post_pricing_issue_type(
    payload: PricingIssueTypeCreate,
    _: dict = Depends(require_role("admin", "front_desk")),
) -> PricingIssueTypeResponse:
    try:
        return PricingIssueTypeResponse.model_validate(database.create_pricing_issue_type(payload.model_dump()))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.patch("/catalog/issue-types/{issue_type_id}", response_model=PricingIssueTypeResponse)
def patch_pricing_issue_type(
    issue_type_id: int,
    payload: PricingIssueTypeUpdate,
    _: dict = Depends(require_role("admin", "front_desk")),
) -> PricingIssueTypeResponse:
    try:
        updated = database.update_pricing_issue_type(issue_type_id, payload.model_dump(exclude_none=True))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if updated is None:
        raise HTTPException(status_code=404, detail="Issue type not found")
    return PricingIssueTypeResponse.model_validate(updated)


@router.get("/catalog/repair-types", response_model=list[PricingRepairTypeResponse])
def get_pricing_repair_types(include_inactive: bool = True) -> list[PricingRepairTypeResponse]:
    return database.list_pricing_repair_types(include_inactive=include_inactive)


@router.post("/catalog/repair-types", response_model=PricingRepairTypeResponse, status_code=201)
def post_pricing_repair_type(
    payload: PricingRepairTypeCreate,
    _: dict = Depends(require_role("admin", "front_desk")),
) -> PricingRepairTypeResponse:
    try:
        return PricingRepairTypeResponse.model_validate(database.create_pricing_repair_type(payload.model_dump()))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.patch("/catalog/repair-types/{repair_type_id}", response_model=PricingRepairTypeResponse)
def patch_pricing_repair_type(
    repair_type_id: int,
    payload: PricingRepairTypeUpdate,
    _: dict = Depends(require_role("admin", "front_desk")),
) -> PricingRepairTypeResponse:
    try:
        updated = database.update_pricing_repair_type(repair_type_id, payload.model_dump(exclude_none=True))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if updated is None:
        raise HTTPException(status_code=404, detail="Repair type not found")
    return PricingRepairTypeResponse.model_validate(updated)


@router.get("/catalog/rules", response_model=list[PricingRuleResponse])
def get_pricing_rules_catalog(
    include_inactive: bool = True,
    search: str | None = None,
    brand_id: int | None = None,
    model_id: int | None = None,
    issue_type_id: int | None = None,
    repair_type_id: int | None = None,
) -> list[PricingRuleResponse]:
    return database.list_pricing_rules(
        {
            "include_inactive": include_inactive,
            "search": search,
            "brand_id": brand_id,
            "model_id": model_id,
            "issue_type_id": issue_type_id,
            "repair_type_id": repair_type_id,
        }
    )


@router.post("/catalog/rules", response_model=PricingRuleResponse, status_code=201)
def post_pricing_rule(
    payload: PricingRuleCreate,
    _: dict = Depends(require_role("admin", "front_desk")),
) -> PricingRuleResponse:
    try:
        return PricingRuleResponse.model_validate(database.create_pricing_rule(payload.model_dump()))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.patch("/catalog/rules/{rule_id}", response_model=PricingRuleResponse)
def patch_pricing_rule(
    rule_id: int,
    payload: PricingRuleUpdate,
    _: dict = Depends(require_role("admin", "front_desk")),
) -> PricingRuleResponse:
    try:
        updated = database.update_pricing_rule(rule_id, payload.model_dump(exclude_none=True))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if updated is None:
        raise HTTPException(status_code=404, detail="Pricing rule not found")
    return PricingRuleResponse.model_validate(updated)


@router.delete("/catalog/rules/{rule_id}", status_code=204)
def delete_pricing_rule(
    rule_id: int,
    _: dict = Depends(require_role("admin", "front_desk")),
) -> None:
    deleted = database.delete_pricing_rule(rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Pricing rule not found")


@router.get("/catalog/suggest", response_model=PricingRuleSuggestionResponse)
def get_pricing_suggestion(brand: str, model: str, issue_type: str) -> PricingRuleSuggestionResponse:
    rule = database.get_pricing_rule_suggestion(brand=brand, model=model, issue_type=issue_type)
    if rule is None:
        return PricingRuleSuggestionResponse(match_found=False, rule=None)
    return PricingRuleSuggestionResponse(match_found=True, rule=PricingRuleResponse.model_validate(rule))
