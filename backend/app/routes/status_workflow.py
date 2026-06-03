from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_role
from app.models import StatusWorkflowRulesResponse, StatusWorkflowRulesUpdate
from app.services.status_workflow import StatusWorkflowService


router = APIRouter(prefix="/api/status-workflow", tags=["status-workflow"])


@router.get("", response_model=StatusWorkflowRulesResponse)
def get_status_workflow_rules(
    _: dict = Depends(require_role("owner", "admin", "front_desk", "technician", "viewer")),
) -> StatusWorkflowRulesResponse:
    return StatusWorkflowRulesResponse.model_validate(StatusWorkflowService.get_rules())


@router.patch("", response_model=StatusWorkflowRulesResponse)
def patch_status_workflow_rules(
    payload: StatusWorkflowRulesUpdate,
    _: dict = Depends(require_role("owner", "admin")),
) -> StatusWorkflowRulesResponse:
    try:
        rules = StatusWorkflowService.update_rules(payload.model_dump(exclude_none=True))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return StatusWorkflowRulesResponse.model_validate(rules)
