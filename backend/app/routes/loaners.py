from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import require_role
from app.services.loaner import LoanerService
from app.models import (
    LoanerCheckoutCreate,
    LoanerCheckoutResponse,
    LoanerPhoneCreate,
    LoanerPhoneResponse,
    LoanerPhoneUpdate,
    LoanerReturnRequest,
)

router = APIRouter(prefix="/api/loaners", tags=["loaners"])

@router.get("", response_model=list[LoanerPhoneResponse])
def get_loaners(status: str | None = Query(default=None)) -> list[LoanerPhoneResponse]:
    loaners = LoanerService.list_loaners(status=status)
    return [LoanerPhoneResponse.model_validate(item) for item in loaners]

@router.post("", response_model=LoanerPhoneResponse, status_code=201)
def post_loaner(
    payload: LoanerPhoneCreate,
    _: dict = Depends(require_role("admin", "front_desk")),
) -> LoanerPhoneResponse:
    try:
        loaner = LoanerService.create_loaner(payload.model_dump())
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return LoanerPhoneResponse.model_validate(loaner)

@router.get("/{loaner_id}", response_model=LoanerPhoneResponse)
def get_loaner_by_id(loaner_id: int) -> LoanerPhoneResponse:
    loaner = LoanerService.get_loaner(loaner_id)
    if loaner is None:
        raise HTTPException(status_code=404, detail="Loaner not found")
    return LoanerPhoneResponse.model_validate(loaner)

@router.patch("/{loaner_id}", response_model=LoanerPhoneResponse)
def patch_loaner(
    loaner_id: int,
    payload: LoanerPhoneUpdate,
    _: dict = Depends(require_role("admin", "front_desk", "technician")),
) -> LoanerPhoneResponse:
    loaner = LoanerService.update_loaner(loaner_id, payload.model_dump(exclude_unset=True))
    if loaner is None:
        raise HTTPException(status_code=404, detail="Loaner not found")
    return LoanerPhoneResponse.model_validate(loaner)

@router.post("/{loaner_id}/checkout", response_model=LoanerCheckoutResponse, status_code=201)
def post_loaner_checkout(
    loaner_id: int,
    payload: LoanerCheckoutCreate,
    _: dict = Depends(require_role("admin", "front_desk")),
) -> LoanerCheckoutResponse:
    try:
        checkout = LoanerService.checkout_loaner(loaner_id, payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if checkout is None:
        raise HTTPException(status_code=404, detail="Loaner not found")
    return LoanerCheckoutResponse.model_validate(checkout)

@router.post("/{loaner_id}/return", response_model=LoanerCheckoutResponse)
def post_loaner_return(
    loaner_id: int,
    payload: LoanerReturnRequest,
    _: dict = Depends(require_role("admin", "front_desk", "technician")),
) -> LoanerCheckoutResponse:
    try:
        checkout = LoanerService.return_loaner(loaner_id, payload.model_dump())
    except ValueError as error:
        if str(error) == "Loaner not found":
            raise HTTPException(status_code=404, detail=str(error)) from error
        raise HTTPException(status_code=400, detail=str(error)) from error
    return LoanerCheckoutResponse.model_validate(checkout)

@router.get("/overdue/list", response_model=list[LoanerCheckoutResponse])
def get_overdue_loaners() -> list[LoanerCheckoutResponse]:
    overdue = LoanerService.list_overdue_loaners()
    return [LoanerCheckoutResponse.model_validate(item) for item in overdue]