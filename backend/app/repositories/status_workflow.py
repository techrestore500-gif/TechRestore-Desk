"""Repository for status workflow rule settings."""
from app.database import get_status_workflow_rules, update_status_workflow_rules


class StatusWorkflowRepository:
    """Data access for status workflow rules."""

    @staticmethod
    def get_rules() -> dict:
        return get_status_workflow_rules()

    @staticmethod
    def update_rules(payload: dict) -> dict:
        return update_status_workflow_rules(payload)
