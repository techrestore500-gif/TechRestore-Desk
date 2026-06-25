from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import require_role
from app.models import RepairCategoryCreate, RepairCategoryResponse, RepairCategoryUpdate
from app.services.repair_categories import RepairCategoryService


router = APIRouter(prefix="/api/repair-categories", tags=["repair-categories"])


@router.get("", response_model=list[RepairCategoryResponse])
def get_repair_categories(
    include_inactive: bool = Query(default=False),
    _: dict = Depends(require_role("owner", "admin", "manager", "front_desk", "technician", "viewer")),
) -> list[RepairCategoryResponse]:
    categories = RepairCategoryService.list_categories(include_inactive=include_inactive)
    return [RepairCategoryResponse.model_validate(item) for item in categories]


@router.post("", response_model=RepairCategoryResponse, status_code=201)
def post_repair_category(
    payload: RepairCategoryCreate,
    _: dict = Depends(require_role("owner", "admin", "manager")),
) -> RepairCategoryResponse:
    try:
        category = RepairCategoryService.create_category(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return RepairCategoryResponse.model_validate(category)


@router.patch("/{repair_category_id}", response_model=RepairCategoryResponse)
def patch_repair_category(
    repair_category_id: int,
    payload: RepairCategoryUpdate,
    _: dict = Depends(require_role("owner", "admin", "manager")),
) -> RepairCategoryResponse:
    try:
        category = RepairCategoryService.update_category(repair_category_id, payload.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if category is None:
        raise HTTPException(status_code=404, detail="Repair category not found")
    return RepairCategoryResponse.model_validate(category)
