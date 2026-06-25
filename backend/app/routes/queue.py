"""
Technician queue endpoints.

Provides queue view of tickets grouped by status for optimized technician workflow.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_role
from app.models import QueueAssignmentRequest, QueueAssignmentResponse, QueueTicketResponse
from app.services.queue import QueueService

router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("/", response_model=dict)
async def get_queue() -> dict:
    """
    Get tickets grouped by status for technician queue.
    
    Queue priorities:
    1. Loaner Outstanding — customer has overdue loaner
    2. Waiting for Parts — blocked on parts, needs follow-up
    3. Customer Approval Needed — blocked on customer approval
    4. New Intake — just arrived, needs triage
    5. Needs Diagnosis — awaiting technician review
    
    Returns:
        {
            "Loaner Outstanding": [
                {
                    "id": 5,
                    "ticket_number": "TR-00005",
                    "customer_name": "John Doe",
                    "customer_phone": "732-555-1234",
                    "manufacturer": "Kyocera",
                    "model_name": "E4610",
                    "issue_category": "Broken screen",
                    "status": "In Repair",
                    "customer_approval_limit": 50,
                    "assigned_technician": "Bob",
                    "intake_date": "2026-05-07T10:00:00",
                    "created_at": "2026-05-07T10:00:00"
                }
            ],
            "Waiting for Parts": [...],
            "Customer Approval Needed": [...],
            "New Intake": [...],
            "Needs Diagnosis": [...]
        }
    """
    queue = QueueService.get_queue()
    
    # Convert each ticket to proper response format
    formatted_queue = {}
    for status, tickets in queue.items():
        formatted_queue[status] = [
            QueueTicketResponse(
                id=t["id"],
                ticket_number=t["ticket_number"],
                customer_id=t["customer_id"],
                customer_name=t["customer_name"],
                customer_phone=t["customer_phone"],
                manufacturer=t["manufacturer"],
                model_name=t["model_name"],
                issue_category=t["issue_category"],
                status=t["status"],
                customer_approval_limit=t["customer_approval_limit"],
                assigned_technician=t["assigned_technician"],
                intake_date=t["intake_date"],
                created_at=t["created_at"],
            ).model_dump()
            for t in tickets
        ]
    
    return formatted_queue


@router.post("/assign", response_model=QueueAssignmentResponse)
async def assign_ticket_in_queue(
    payload: QueueAssignmentRequest,
    _: dict = Depends(require_role("admin", "manager", "front_desk", "technician")),
) -> QueueAssignmentResponse:
    result = QueueService.assign_ticket(
        ticket_id=payload.ticket_id,
        assigned_technician=payload.assigned_technician,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return QueueAssignmentResponse(**result)
