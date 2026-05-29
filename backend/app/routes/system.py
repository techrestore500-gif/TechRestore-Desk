from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import Response

from app.auth.dependencies import require_role
from app.models import (
    AuditLogListResponse,
    BackupResponse,
    JobDeadLetterResponse,
    LoanerAgreementDefaultsResponse,
    LoanerAgreementDefaultsUpdate,
    NotificationTemplate,
    NotificationTemplatesUpdate,
    QueryMetricsResponse,
    RuntimeDiagnosticsResponse,
    SystemActivityResponse,
)
from app.services.system import SystemService

router = APIRouter(prefix="/api/system", tags=["system"])


@router.post("/backup", response_model=BackupResponse)
def create_backup() -> BackupResponse:
    return SystemService.create_backup()


@router.get("/history", response_model=list[SystemActivityResponse])
def get_history() -> list[SystemActivityResponse]:
    return SystemService.list_history()


@router.get("/export")
def export_snapshot() -> Response:
    file_name, payload = SystemService.export_snapshot()
    return Response(
        content=payload,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@router.get("/loaner-agreement-defaults", response_model=LoanerAgreementDefaultsResponse)
def get_loaner_agreement_defaults() -> LoanerAgreementDefaultsResponse:
    return SystemService.get_loaner_agreement_defaults()


@router.patch("/loaner-agreement-defaults", response_model=LoanerAgreementDefaultsResponse)
def patch_loaner_agreement_defaults(payload: LoanerAgreementDefaultsUpdate) -> LoanerAgreementDefaultsResponse:
    return SystemService.update_loaner_agreement_defaults(payload.model_dump(exclude_none=True))


@router.get("/notification-templates", response_model=list[NotificationTemplate])
def get_notification_templates() -> list[NotificationTemplate]:
    return SystemService.get_notification_templates()


@router.patch("/notification-templates", response_model=list[NotificationTemplate])
def patch_notification_templates(payload: dict = Body(...)) -> list[NotificationTemplate]:
    return SystemService.update_notification_templates(payload)


@router.get("/jobs/dead-letters", response_model=list[JobDeadLetterResponse])
def get_dead_letters(
    limit: int = Query(default=100, ge=1, le=500),
    _: dict = Depends(require_role("admin")),
) -> list[JobDeadLetterResponse]:
    return SystemService.list_dead_letters(limit=limit)


@router.post("/jobs/scan-overdue-loaners")
def post_scan_overdue_loaners(_: dict = Depends(require_role("admin"))) -> dict:
    return SystemService.trigger_overdue_scan()


@router.get("/audit-logs", response_model=AuditLogListResponse)
def get_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    _: dict = Depends(require_role("admin")),
) -> AuditLogListResponse:
    return SystemService.list_audit_logs(
        page=page,
        page_size=page_size,
        action=action,
        entity_type=entity_type,
    )


@router.get("/performance/query-metrics", response_model=QueryMetricsResponse)
def get_query_metrics(_: dict = Depends(require_role("admin"))) -> QueryMetricsResponse:
    return SystemService.get_query_metrics()


@router.post("/performance/query-metrics/reset")
def post_reset_query_metrics(_: dict = Depends(require_role("admin"))) -> dict:
    return SystemService.reset_query_metrics()


@router.get("/runtime-diagnostics", response_model=RuntimeDiagnosticsResponse)
def get_runtime_diagnostics(_: dict = Depends(require_role("admin"))) -> RuntimeDiagnosticsResponse:
    return SystemService.get_runtime_diagnostics()
