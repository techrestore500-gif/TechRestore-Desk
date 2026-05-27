"""Repository for local system maintenance workflows."""
from app.database import (
    create_database_backup,
    export_database_snapshot,
    get_loaner_agreement_defaults,
    get_notification_templates,
    list_system_activity,
    update_loaner_agreement_defaults,
    update_notification_templates,
)


class SystemRepository:
    """Handles backup and export operations."""

    @staticmethod
    def create_backup() -> dict:
        return create_database_backup()

    @staticmethod
    def export_snapshot() -> tuple[str, bytes]:
        return export_database_snapshot()

    @staticmethod
    def list_history() -> list[dict]:
        return list_system_activity()

    @staticmethod
    def get_loaner_agreement_defaults() -> dict:
        return get_loaner_agreement_defaults()

    @staticmethod
    def update_loaner_agreement_defaults(payload: dict) -> dict:
        return update_loaner_agreement_defaults(payload)

    @staticmethod
    def get_notification_templates() -> dict:
        return get_notification_templates()

    @staticmethod
    def update_notification_templates(payload: dict) -> dict:
        return update_notification_templates(payload)
