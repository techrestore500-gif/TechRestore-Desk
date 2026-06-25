from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import require_role
from app.services.ticket import TicketService
from app.models import (
    LoanerAgreementResponse,
    RepairActionCreate,
    RepairActionResponse,
    TicketCreate,
    TicketDetailResponse,
    TicketNoteCreate,
    TicketNoteResponse,
    TicketStatusChange,
    TicketStatusHistoryResponse,
    TicketSummaryListResponse,
    TicketSummaryResponse,
    TicketUpdate,
    TicketCloseRequest,
    TicketCloseResponse,
)


router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.get("", response_model=list[TicketSummaryResponse])
def get_ticket_list(
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    _: dict = Depends(require_role("owner", "admin", "manager", "front_desk", "technician", "viewer")),
) -> list[TicketSummaryResponse]:
    tickets = TicketService.list_tickets(status=status, search=search)
    return [TicketSummaryResponse.model_validate(item) for item in tickets]


@router.get("/paged", response_model=TicketSummaryListResponse)
def get_ticket_list_paged(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    _: dict = Depends(require_role("owner", "admin", "manager", "front_desk", "technician", "viewer")),
) -> TicketSummaryListResponse:
    result = TicketService.list_tickets_paginated(
        page=page,
        page_size=page_size,
        status=status,
        search=search,
    )
    return TicketSummaryListResponse.model_validate(result)


@router.post("", response_model=TicketDetailResponse, status_code=201)
def post_ticket(
    payload: TicketCreate,
    _: dict = Depends(require_role("owner", "admin", "manager", "front_desk", "technician")),
) -> TicketDetailResponse:
    try:
        ticket = TicketService.create_ticket(payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return TicketDetailResponse.model_validate(ticket)


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket_by_id(
    ticket_id: int,
    _: dict = Depends(require_role("owner", "admin", "manager", "front_desk", "technician", "viewer")),
) -> TicketDetailResponse:
    ticket = TicketService.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return TicketDetailResponse.model_validate(ticket)


@router.get("/{ticket_id}/loaner-agreement", response_model=LoanerAgreementResponse)
def get_ticket_loaner_agreement(
    ticket_id: int,
    _: dict = Depends(require_role("owner", "admin", "manager", "front_desk", "technician", "viewer")),
) -> LoanerAgreementResponse:
    agreement = TicketService.get_ticket_loaner_agreement(ticket_id)
    if agreement is None:
        raise HTTPException(status_code=404, detail="Loaner agreement not found")
    return LoanerAgreementResponse.model_validate(agreement)


@router.patch("/{ticket_id}", response_model=TicketDetailResponse)
def patch_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    _: dict = Depends(require_role("admin", "manager", "front_desk", "technician")),
) -> TicketDetailResponse:
    updates = payload.model_dump(exclude_unset=True)
    try:
        ticket = TicketService.update_ticket(ticket_id, updates)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return TicketDetailResponse.model_validate(ticket)


@router.post("/{ticket_id}/status", response_model=TicketStatusHistoryResponse, status_code=201)
def post_ticket_status(
    ticket_id: int,
    payload: TicketStatusChange,
    _: dict = Depends(require_role("admin", "manager", "front_desk", "technician")),
) -> TicketStatusHistoryResponse:
    try:
        history_item = TicketService.update_ticket_status(ticket_id, payload.model_dump())
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return TicketStatusHistoryResponse.model_validate(history_item)


@router.get("/{ticket_id}/history", response_model=list[TicketStatusHistoryResponse])
def get_ticket_status_history(
    ticket_id: int,
    _: dict = Depends(require_role("owner", "admin", "manager", "front_desk", "technician", "viewer")),
) -> list[TicketStatusHistoryResponse]:
    try:
        items = TicketService.get_ticket_history(ticket_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return [TicketStatusHistoryResponse.model_validate(item) for item in items]


@router.post("/{ticket_id}/notes", response_model=TicketNoteResponse, status_code=201)
def post_ticket_note(
    ticket_id: int,
    payload: TicketNoteCreate,
    _: dict = Depends(require_role("admin", "manager", "front_desk", "technician")),
) -> TicketNoteResponse:
    try:
        note = TicketService.add_ticket_note(ticket_id, payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return TicketNoteResponse.model_validate(note)


@router.get("/{ticket_id}/notes", response_model=list[TicketNoteResponse])
def get_ticket_note_list(
    ticket_id: int,
    _: dict = Depends(require_role("owner", "admin", "manager", "front_desk", "technician", "viewer")),
) -> list[TicketNoteResponse]:
    try:
        items = TicketService.get_ticket_notes(ticket_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return [TicketNoteResponse.model_validate(item) for item in items]

@router.post("/{ticket_id}/close", response_model=TicketCloseResponse)
def post_ticket_close(
    ticket_id: int,
    payload: TicketCloseRequest,
    _: dict = Depends(require_role("admin", "manager", "front_desk", "technician")),
) -> TicketCloseResponse:
    try:
        result = TicketService.close_ticket(ticket_id, payload.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if result is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return TicketCloseResponse.model_validate(result)


@router.post("/{ticket_id}/repair-actions", response_model=RepairActionResponse, status_code=201)
def post_repair_action(
    ticket_id: int,
    payload: RepairActionCreate,
    _: dict = Depends(require_role("admin", "manager", "technician")),
) -> RepairActionResponse:
    try:
        item = TicketService.add_repair_action(ticket_id, payload.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return RepairActionResponse.model_validate(item)


@router.get("/{ticket_id}/repair-actions", response_model=list[RepairActionResponse])
def get_repair_action_list(
    ticket_id: int,
    _: dict = Depends(require_role("owner", "admin", "manager", "front_desk", "technician", "viewer")),
) -> list[RepairActionResponse]:
    try:
        items = TicketService.get_repair_actions(ticket_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return [RepairActionResponse.model_validate(item) for item in items]