"""Repository for supported device models."""
from app.database import list_supported_models


class SupportedModelRepository:
    """Handles supported device model data access."""

    @staticmethod
    def list_models() -> list[dict]:
        return list_supported_models()
