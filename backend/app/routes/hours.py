"""
Technician hours logging and reporting endpoints.

Tracks time spent on repairs and provides aggregated reporting by technician and date.
"""

from fastapi import APIRouter, HTTPException, Query

from app.services.hours import HoursService
from app.models import (
    HoursClockInRequest,
    HoursClockOutRequest,
    HoursClockOutResponse,
    HoursClockSessionResponse,
    HoursLogCreate,
    HoursLogResponse,
    HoursSummaryResponse,
)

router = APIRouter(prefix="/hours", tags=["hours"])


@router.get("/active", response_model=HoursClockSessionResponse | None)
async def get_active_hours_session(
    technician: str = Query(..., description="Technician name for active session lookup"),
) -> HoursClockSessionResponse | None:
    session = HoursService.get_active_session(technician=technician)
    return HoursClockSessionResponse(**session) if session else None


@router.post("/clock-in", response_model=HoursClockSessionResponse, status_code=201)
async def clock_in_hours(req: HoursClockInRequest) -> HoursClockSessionResponse:
    try:
        result = HoursService.clock_in(req.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return HoursClockSessionResponse(**result)


@router.post("/clock-out", response_model=HoursClockOutResponse)
async def clock_out_hours(req: HoursClockOutRequest) -> HoursClockOutResponse:
    try:
        result = HoursService.clock_out(req.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return HoursClockOutResponse(**result)


@router.post("/", response_model=HoursLogResponse, status_code=201)
async def create_hours(req: HoursLogCreate) -> HoursLogResponse:
    """
    Log technician hours for a date and optional ticket.
    
    Request:
        {
            "technician": "Bob",
            "work_date": "2026-05-07",
            "hours_worked": 1.5,
            "work_description": "Screen replacement",
            "ticket_id": 5  (optional)
        }
    
    Response:
        {
            "id": 1,
            "ticket_id": 5,
            "technician": "Bob",
            "work_date": "2026-05-07",
            "hours_worked": 1.5,
            "work_description": "Screen replacement",
            "created_at": "2026-05-07T12:00:00",
            "updated_at": "2026-05-07T12:00:00"
        }
    """
    payload = req.model_dump()
    try:
        result = HoursService.create_hours(payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return HoursLogResponse(**result)


@router.get("/", response_model=list[HoursLogResponse])
async def list_hours_entries(
    start_date: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    technician: str | None = Query(None, description="Filter by technician name"),
) -> list[HoursLogResponse]:
    """
    List hours entries with optional filtering.
    
    Query parameters:
        - start_date: ISO date string (inclusive), e.g., "2026-05-01"
        - end_date: ISO date string (inclusive), e.g., "2026-05-07"
        - technician: Filter by exact technician name, e.g., "Bob"
    
    Returns: List of hours entries sorted by date descending, then technician ascending
    """
    results = HoursService.list_hours(start_date=start_date, end_date=end_date, technician=technician)
    return [HoursLogResponse(**r) for r in results]


@router.get("/summary", response_model=HoursSummaryResponse)
async def get_hours_summary_endpoint(
    start_date: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    technician: str | None = Query(None, description="Filter by technician name"),
) -> HoursSummaryResponse:
    """
    Get aggregated hours summary by technician and overall total.
    
    Query parameters:
        - start_date: ISO date string (inclusive), e.g., "2026-05-01"
        - end_date: ISO date string (inclusive), e.g., "2026-05-07"
    
    Returns:
        {
            "by_technician": {
                "Bob": 8.5,
                "Jane": 6.5
            },
            "total_hours": 15.0,
            "date_range": {
                "start": "2026-05-01",
                "end": "2026-05-07"
            }
        }
    """
    summary = HoursService.get_summary(start_date=start_date, end_date=end_date, technician=technician)
    return HoursSummaryResponse(**summary)
