"""Service layer for status workflow rule settings."""
from app.repositories.status_workflow import StatusWorkflowRepository


class StatusWorkflowService:
    """Business logic for status workflow settings."""

    @staticmethod
    def get_rules() -> dict:
        return StatusWorkflowRepository.get_rules()

    @staticmethod
    def update_rules(payload: dict) -> dict:
        return StatusWorkflowRepository.update_rules(payload)
