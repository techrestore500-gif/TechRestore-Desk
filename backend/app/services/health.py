"""Service layer for health checks."""
from app.repositories.health import HealthRepository


class HealthService:
    """Business logic for application health checks."""

    @staticmethod
    def get_health_status() -> dict:
        counts = HealthRepository.get_seed_counts()
        database_path = HealthRepository.get_database_path()
        return {
            "status": "ok",
            "app": "Tech Restore Desk",
            "database_ready": database_path.exists(),
            "supported_model_count": counts["supported_model_count"],
            "repair_category_count": counts["repair_category_count"],
        }
