from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.auth.dependencies import require_role
from app.models import (
    DonorCreate,
    DonorResponse,
    DonorUpdate,
    InventoryMovementListResponse,
    InventoryReconciliationRequest,
    InventoryReconciliationResponse,
    InventoryPurchaseCreate,
    InventoryPurchaseListResponse,
    InventoryPurchaseResponse,
    PartCreate,
    PartStockAdjustmentRequest,
    PartHarvestRequest,
    PartResponse,
    PartUpdate,
    PartUsageCreate,
    PartUsageResponse,
)
from app.services.inventory import InventoryService

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("/parts", response_model=list[PartResponse])
def get_parts(
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    low_stock_only: bool = Query(default=False),
) -> list[PartResponse]:
    parts = InventoryService.list_parts(category=category, status=status, low_stock_only=low_stock_only)
    return [PartResponse.model_validate(item) for item in parts]


@router.get("/parts/{part_id}", response_model=PartResponse)
def get_part_by_id(part_id: int) -> PartResponse:
    part = InventoryService.get_part(part_id)
    if part is None:
        raise HTTPException(status_code=404, detail="Part not found")
    return PartResponse.model_validate(part)


@router.post("/parts", response_model=PartResponse, status_code=201)
def post_part(
    payload: PartCreate,
    _: dict = Depends(require_role("admin", "manager", "technician", "front_desk")),
) -> PartResponse:
    try:
        part = InventoryService.create_part(payload.model_dump())
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return PartResponse.model_validate(part)


@router.patch("/parts/{part_id}", response_model=PartResponse)
def patch_part(
    part_id: int,
    payload: PartUpdate,
    _: dict = Depends(require_role("admin", "manager", "technician", "front_desk")),
) -> PartResponse:
    try:
        part = InventoryService.update_part(part_id, payload.model_dump(exclude_unset=True))
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if part is None:
        raise HTTPException(status_code=404, detail="Part not found")
    return PartResponse.model_validate(part)


@router.delete("/parts/{part_id}", status_code=204)
def remove_part(
    part_id: int,
    _: dict = Depends(require_role("admin", "manager", "technician", "front_desk")),
) -> Response:
    if not InventoryService.delete_part(part_id):
        raise HTTPException(status_code=404, detail="Part not found")
    return Response(status_code=204)


@router.post("/parts/usage", response_model=PartUsageResponse, status_code=201)
def post_part_usage(
    payload: PartUsageCreate,
    _: dict = Depends(require_role("admin", "manager", "technician", "front_desk")),
) -> PartUsageResponse:
    try:
        usage = InventoryService.log_part_usage(
            repair_action_id=payload.repair_action_id,
            part_id=payload.part_id,
            quantity_used=payload.quantity_used,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return PartUsageResponse.model_validate(usage)


@router.get("/repair-actions/{repair_action_id}/parts", response_model=list[PartUsageResponse])
def get_repair_action_parts(repair_action_id: int) -> list[PartUsageResponse]:
    usage = InventoryService.get_part_usage_for_repair_action(repair_action_id)
    return [PartUsageResponse.model_validate(item) for item in usage]


@router.get("/parts/{part_id}/usage", response_model=list[PartUsageResponse])
def get_part_usage(part_id: int) -> list[PartUsageResponse]:
    usage = InventoryService.get_part_usage_history(part_id)
    return [PartUsageResponse.model_validate(item) for item in usage]


@router.get("/donors", response_model=list[DonorResponse])
def get_donors(
    status: str | None = Query(default=None),
    device_model: str | None = Query(default=None),
) -> list[DonorResponse]:
    donors = InventoryService.list_donors(status=status, device_model=device_model)
    return [DonorResponse.model_validate(item) for item in donors]


@router.get("/donors/{donor_id}", response_model=DonorResponse)
def get_donor_by_id(donor_id: int) -> DonorResponse:
    donor = InventoryService.get_donor(donor_id)
    if donor is None:
        raise HTTPException(status_code=404, detail="Donor device not found")
    return DonorResponse.model_validate(donor)


@router.post("/donors", response_model=DonorResponse, status_code=201)
def post_donor(
    payload: DonorCreate,
    _: dict = Depends(require_role("admin", "manager", "technician", "front_desk")),
) -> DonorResponse:
    try:
        donor = InventoryService.create_donor(payload.model_dump())
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return DonorResponse.model_validate(donor)


@router.patch("/donors/{donor_id}", response_model=DonorResponse)
def patch_donor(
    donor_id: int,
    payload: DonorUpdate,
    _: dict = Depends(require_role("admin", "manager", "technician", "front_desk")),
) -> DonorResponse:
    try:
        donor = InventoryService.update_donor(donor_id, payload.model_dump(exclude_unset=True))
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if donor is None:
        raise HTTPException(status_code=404, detail="Donor device not found")
    return DonorResponse.model_validate(donor)


@router.post("/donors/{donor_id}/harvest", response_model=DonorResponse)
def post_harvest_part(
    donor_id: int,
    payload: PartHarvestRequest,
    _: dict = Depends(require_role("admin", "manager", "technician", "front_desk")),
) -> DonorResponse:
    try:
        donor = InventoryService.harvest_part_from_donor(donor_id, payload.part_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if donor is None:
        raise HTTPException(status_code=404, detail="Donor device not found")
    return DonorResponse.model_validate(donor)


@router.get("/low-stock", response_model=list[PartResponse])
def get_low_stock() -> list[PartResponse]:
    parts = InventoryService.get_low_stock_parts()
    return [PartResponse.model_validate(item) for item in parts]


@router.get("/purchases", response_model=InventoryPurchaseListResponse)
def get_inventory_purchases() -> InventoryPurchaseListResponse:
    items = InventoryService.list_purchases()
    return InventoryPurchaseListResponse(items=[InventoryPurchaseResponse.model_validate(item) for item in items])


@router.get("/purchases/{purchase_id}", response_model=InventoryPurchaseResponse)
def get_inventory_purchase_by_id(purchase_id: int) -> InventoryPurchaseResponse:
    purchase = InventoryService.get_purchase(purchase_id)
    if purchase is None:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return InventoryPurchaseResponse.model_validate(purchase)


@router.post("/purchases", response_model=InventoryPurchaseResponse, status_code=201)
def post_inventory_purchase(
    payload: InventoryPurchaseCreate,
    _: dict = Depends(require_role("admin", "manager", "technician", "front_desk")),
) -> InventoryPurchaseResponse:
    try:
        purchase = InventoryService.create_purchase(payload.model_dump())
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return InventoryPurchaseResponse.model_validate(purchase)


@router.post("/parts/{part_id}/adjust", response_model=PartResponse)
def post_part_stock_adjustment(
    part_id: int,
    payload: PartStockAdjustmentRequest,
    _: dict = Depends(require_role("admin", "manager", "technician", "front_desk")),
) -> PartResponse:
    try:
        part = InventoryService.adjust_part_stock(
            part_id=part_id,
            quantity_delta=payload.quantity_delta,
            movement_type=payload.movement_type,
            reason=payload.reason,
            ticket_id=payload.ticket_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return PartResponse.model_validate(part)


@router.get("/movements", response_model=InventoryMovementListResponse)
def get_inventory_movements(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    part_id: int | None = Query(default=None),
    movement_type: str | None = Query(default=None),
) -> InventoryMovementListResponse:
    result = InventoryService.list_movements(
        page=page,
        page_size=page_size,
        part_id=part_id,
        movement_type=movement_type,
    )
    return InventoryMovementListResponse.model_validate(result)


@router.post("/reconciliation", response_model=InventoryReconciliationResponse, status_code=201)
def post_inventory_reconciliation(
    payload: InventoryReconciliationRequest,
    _: dict = Depends(require_role("admin", "manager", "technician", "front_desk")),
) -> InventoryReconciliationResponse:
    try:
        record = InventoryService.reconcile_stock(
            part_id=payload.part_id,
            actual_quantity=payload.actual_quantity,
            reason=payload.reason,
            apply_adjustment=payload.apply_adjustment,
            resolved_by=payload.resolved_by,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return InventoryReconciliationResponse.model_validate(record)


@router.get("/reconciliation", response_model=list[InventoryReconciliationResponse])
def get_inventory_reconciliation(part_id: int | None = Query(default=None)) -> list[InventoryReconciliationResponse]:
    records = InventoryService.list_reconciliations(part_id=part_id)
    return [InventoryReconciliationResponse.model_validate(item) for item in records]
