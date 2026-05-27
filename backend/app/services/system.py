"""Service layer for local backup and export workflows."""
from app.models import (
    AuditLogListResponse,
    AuditLogResponse,
    BackupResponse,
    JobDeadLetterResponse,
    LoanerAgreementDefaultsResponse,
    NotificationTemplate,
    NotificationTemplatesUpdate,
    QueryMetricsResponse,
    SystemActivityResponse,
)
from app.core.query_metrics import query_metrics_registry
from app.database import SLOW_QUERY_THRESHOLD_MS
from app.jobs.queue import JobPriority, job_queue
from app.repositories.activity_log import ActivityLogRepository
from app.repositories.jobs import JobsRepository
from app.repositories.system import SystemRepository
from app.services.audit import AuditService


class SystemService:
    """Business logic for local system maintenance actions."""

    @staticmethod
    def create_backup() -> BackupResponse:
        return BackupResponse.model_validate(SystemRepository.create_backup())

    @staticmethod
    def export_snapshot() -> tuple[str, bytes]:
        return SystemRepository.export_snapshot()

    @staticmethod
    def list_history() -> list[SystemActivityResponse]:
        return [SystemActivityResponse.model_validate(item) for item in SystemRepository.list_history()]

    @staticmethod
    def get_loaner_agreement_defaults() -> LoanerAgreementDefaultsResponse:
        return LoanerAgreementDefaultsResponse.model_validate(SystemRepository.get_loaner_agreement_defaults())

    @staticmethod
    def update_loaner_agreement_defaults(payload: dict) -> LoanerAgreementDefaultsResponse:
        before = SystemRepository.get_loaner_agreement_defaults()
        after = SystemRepository.update_loaner_agreement_defaults(payload)
        AuditService.log(
            entity_type="system_config",
            entity_id=1,
            action="admin_loaner_agreement_defaults_updated",
            old_value=before,
            new_value=after,
        )
        return LoanerAgreementDefaultsResponse.model_validate(after)

    @staticmethod
    def get_notification_templates() -> list[NotificationTemplate]:
        templates_dict = SystemRepository.get_notification_templates()
        return [NotificationTemplate.model_validate(t) for t in templates_dict.values()]

    @staticmethod
    def update_notification_templates(payload: dict) -> list[NotificationTemplate]:
        before = SystemRepository.get_notification_templates()
        templates_dict = SystemRepository.update_notification_templates(payload)
        AuditService.log(
            entity_type="notification_templates",
            entity_id=None,
            action="admin_notification_templates_updated",
            old_value=before,
            new_value=templates_dict,
        )
        return [NotificationTemplate.model_validate(t) for t in templates_dict.values()]

    @staticmethod
    def list_dead_letters(limit: int = 100) -> list[JobDeadLetterResponse]:
        return [JobDeadLetterResponse.model_validate(item) for item in JobsRepository.list_dead_letters(limit=limit)]

    @staticmethod
    def trigger_overdue_scan() -> dict:
        return job_queue.enqueue(
            job_name="scan_overdue_loaners",
            payload={"trigger": "manual"},
            queue=JobPriority.DEFAULT,
        )

    @staticmethod
    def list_audit_logs(
        *,
        page: int = 1,
        page_size: int = 50,
        action: str | None = None,
        entity_type: str | None = None,
    ) -> AuditLogListResponse:
        result = ActivityLogRepository.list_paginated(
            page=page,
            page_size=page_size,
            action=action,
            entity_type=entity_type,
        )
        result["items"] = [AuditLogResponse.model_validate(item).model_dump() for item in result["items"]]
        return AuditLogListResponse.model_validate(result)

    @staticmethod
    def get_query_metrics() -> QueryMetricsResponse:
        snapshot = query_metrics_registry.snapshot(SLOW_QUERY_THRESHOLD_MS)
        return QueryMetricsResponse.model_validate(
            {
                "total_queries": snapshot.total_queries,
                "total_duration_ms": snapshot.total_duration_ms,
                "average_duration_ms": snapshot.average_duration_ms,
                "slow_query_count": snapshot.slow_query_count,
                "slow_threshold_ms": snapshot.slow_threshold_ms,
                "top_slowest": snapshot.top_slowest,
            }
        )

    @staticmethod
    def reset_query_metrics() -> dict:
        query_metrics_registry.reset()
        return {"reset": True}
