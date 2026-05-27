from fastapi import APIRouter, HTTPException

from app.models import StatusWorkflowRulesResponse, StatusWorkflowRulesUpdate
from app.services.status_workflow import StatusWorkflowService


router = APIRouter(prefix="/api/status-workflow", tags=["status-workflow"])


@router.get("", response_model=StatusWorkflowRulesResponse)
def get_status_workflow_rules() -> StatusWorkflowRulesResponse:
    return StatusWorkflowRulesResponse.model_validate(StatusWorkflowService.get_rules())


@router.patch("", response_model=StatusWorkflowRulesResponse)
def patch_status_workflow_rules(payload: StatusWorkflowRulesUpdate) -> StatusWorkflowRulesResponse:
    try:
        rules = StatusWorkflowService.update_rules(payload.model_dump(exclude_none=True))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return StatusWorkflowRulesResponse.model_validate(rules)
