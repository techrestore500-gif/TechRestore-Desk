from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import require_role
from app.models import CustomerCreate, CustomerResponse, CustomerUpdate, TicketSummaryResponse
from app.services.customers import CustomerService


router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("", response_model=list[CustomerResponse])
def get_customers(
    search: str | None = Query(default=None),
    _: dict = Depends(require_role("owner", "admin", "front_desk", "technician", "viewer")),
) -> list[CustomerResponse]:
    customers = CustomerService.list_customers(search)
    return [CustomerResponse.model_validate(item) for item in customers]


@router.post("", response_model=CustomerResponse, status_code=201)
def post_customer(
    payload: CustomerCreate,
    _: dict = Depends(require_role("owner", "admin", "front_desk", "technician")),
) -> CustomerResponse:
    return CustomerResponse.model_validate(CustomerService.create_customer(payload.model_dump()))


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer_by_id(
    customer_id: int,
    _: dict = Depends(require_role("owner", "admin", "front_desk", "technician", "viewer")),
) -> CustomerResponse:
    customer = CustomerService.get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CustomerResponse.model_validate(customer)


@router.patch("/{customer_id}", response_model=CustomerResponse)
def patch_customer(
    customer_id: int,
    payload: CustomerUpdate,
    _: dict = Depends(require_role("owner", "admin", "front_desk", "technician")),
) -> CustomerResponse:
    updates = payload.model_dump(exclude_unset=True)
    customer = CustomerService.update_customer(customer_id, updates)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CustomerResponse.model_validate(customer)


@router.get("/{customer_id}/tickets", response_model=list[TicketSummaryResponse])
def get_customer_ticket_list(
    customer_id: int,
    _: dict = Depends(require_role("owner", "admin", "front_desk", "technician", "viewer")),
) -> list[TicketSummaryResponse]:
    if CustomerService.get_customer(customer_id) is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    tickets = CustomerService.list_customer_tickets(customer_id)
    return [TicketSummaryResponse.model_validate(item) for item in tickets]