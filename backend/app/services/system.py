"""Service layer for local backup and export workflows."""
import os
import shutil
from pathlib import Path

import app.database as database
from app.core.settings import get_settings
from app.models import (
    AuditLogListResponse,
    AuditLogResponse,
    BackupResponse,
    JobDeadLetterResponse,
    LoanerAgreementDefaultsResponse,
    NotificationTemplate,
    NotificationTemplatesUpdate,
    QueryMetricsResponse,
    RuntimeDiagnosticsResponse,
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
    def create_backup(*, requested_by: dict | None = None) -> BackupResponse:
        requested_by_user_id = requested_by.get("id") if isinstance(requested_by, dict) and isinstance(requested_by.get("id"), int) else None
        backup = SystemRepository.create_backup(requested_by_user_id=requested_by_user_id)
        response = BackupResponse.model_validate(
            {
                **backup,
                "backup_path": backup.get("backup_path_public") or backup.get("backup_path"),
            }
        )
        AuditService.log(
            entity_type="system_backup",
            entity_id=None,
            action="admin_backup_created",
            new_value={
                "file_name": response.file_name,
                "created_at": response.created_at,
                "file_size_bytes": response.file_size_bytes,
                "integrity_check": response.integrity_check,
                "requested_by_user_id": requested_by_user_id,
            },
            user_id=requested_by_user_id,
        )
        return response

    @staticmethod
    def get_backup_file_path(file_name: str) -> Path:
        return SystemRepository.get_backup_file_path(file_name)

    @staticmethod
    def audit_backup_download(*, file_name: str, requested_by: dict | None = None) -> None:
        requested_by_user_id = requested_by.get("id") if isinstance(requested_by, dict) and isinstance(requested_by.get("id"), int) else None
        AuditService.log(
            entity_type="system_backup",
            entity_id=None,
            action="admin_backup_downloaded",
            new_value={"file_name": file_name, "requested_by_user_id": requested_by_user_id},
            user_id=requested_by_user_id,
        )

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

    @staticmethod
    def get_runtime_diagnostics() -> RuntimeDiagnosticsResponse:
        def _public_storage_path(raw: Path) -> str:
            resolved = raw.resolve()
            if database._is_persistent_storage_path(resolved):
                persistent_root = Path(database.PERSISTENT_DATA_ROOT).resolve()
                if database._is_under_path(resolved, persistent_root):
                    relative = resolved.relative_to(persistent_root).as_posix()
                elif resolved.as_posix().lower().startswith("/var/data/"):
                    relative = resolved.relative_to(Path("/var/data")).as_posix()
                else:
                    relative = resolved.name
                return f"persistent:/{relative}"

            persistent_root = Path(database.PERSISTENT_DATA_ROOT).resolve()
            persistent_prefix = persistent_root.as_posix().lower().rstrip("/") + "/"
            resolved_str = resolved.as_posix().lower()
            if resolved_str.startswith(persistent_prefix):
                relative = resolved.relative_to(persistent_root).as_posix()
                return f"persistent:/{relative}"
            return f"local:/{resolved.name}"

        database_url = os.getenv("DATABASE_URL", "").strip()
        database_path_resolved = Path(database.DB_PATH).resolve()
        database_path = _public_storage_path(database_path_resolved)
        is_sqlite = True
        sqlite_under_var_data = database._is_persistent_storage_path(database_path_resolved) if is_sqlite else None
        persistence_status = "persistent_disk" if sqlite_under_var_data else "ephemeral_or_unknown"
        warning = None
        if is_sqlite and not sqlite_under_var_data:
            warning = "SQLite database path is not under persistent storage; redeploys may wipe data."

        backend_commit = os.getenv("RENDER_GIT_COMMIT", "").strip() or None
        frontend_commit = os.getenv("FRONTEND_GIT_COMMIT", "").strip() or backend_commit
        backend_version = os.getenv("APP_VERSION", "").strip() or "local-dev"
        environment = os.getenv("TECH_RESTORE_APP_ENV", "").strip() or os.getenv("APP_ENV", "").strip() or None
        api_base_url = os.getenv("PUBLIC_API_BASE_URL", "").strip() or os.getenv("PUBLIC_BASE_URL", "").strip() or None

        twilio_configured: bool | None = None
        try:
            from app.services.twilio import TwilioService

            setup_status = TwilioService.get_setup_status()
            twilio_configured = bool(
                setup_status.get("twilio_credentials_configured")
                and setup_status.get("public_webhook_base_url_configured")
            )
        except Exception:
            twilio_configured = None

        backups_path_raw = Path(database.BACKUPS_DIR).resolve()
        backups_path = _public_storage_path(backups_path_raw)
        backups_persistent = database._is_persistent_storage_path(backups_path_raw)

        settings = get_settings()
        attachments_path = _public_storage_path(settings.attachments_local_root) if settings.attachments_provider == "local" else "s3"
        attachments_persistent = None
        if settings.attachments_provider == "local":
            attachments_persistent = database._is_persistent_storage_path(settings.attachments_local_root)

        history = SystemRepository.list_history()
        last_backup = next((item for item in history if item.get("activity_type") == "backup"), None)
        last_backup_at = last_backup.get("created_at") if last_backup else None
        last_backup_integrity = None
        if last_backup:
            details = last_backup.get("details") or {}
            if isinstance(details, dict):
                last_backup_integrity = details.get("integrity_check")

        disk_target = Path(database.PERSISTENT_DATA_ROOT)
        try:
            available_disk_bytes = int(shutil.disk_usage(disk_target).free)
        except Exception:
            available_disk_bytes = None

        expected_render_disk_mounted = None
        expected_render_disk_writable = None
        if (os.getenv("RENDER") or "").strip().lower() == "true":
            expected_render_disk_mounted = disk_target.exists() and disk_target.is_dir()
            if expected_render_disk_mounted:
                try:
                    database._assert_directory_writable(disk_target)
                    expected_render_disk_writable = True
                except Exception:
                    expected_render_disk_writable = False

        return RuntimeDiagnosticsResponse.model_validate(
            {
                "database_type": "sqlite",
                "database_path": database_path,
                "database_url_configured": bool(database_url),
                "sqlite_under_var_data": sqlite_under_var_data,
                "persistence_status": persistence_status,
                "warning": warning,
                "backend_online": True,
                "backend_version": backend_version,
                "backend_commit": backend_commit,
                "frontend_commit": frontend_commit,
                "environment": environment,
                "api_base_url": api_base_url,
                "twilio_configured": twilio_configured,
                "backups_path": backups_path,
                "backups_persistent": backups_persistent,
                "attachments_path": attachments_path,
                "attachments_persistent": attachments_persistent,
                "last_backup_at": last_backup_at,
                "last_backup_integrity": last_backup_integrity,
                "available_disk_bytes": available_disk_bytes,
                "expected_render_disk_mounted": expected_render_disk_mounted,
                "expected_render_disk_writable": expected_render_disk_writable,
            }
        )
