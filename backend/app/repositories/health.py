"""Repository for health and seed-count lookups."""
from app.database import DB_PATH, get_seed_counts


class HealthRepository:
    """Handles health-related data access."""

    @staticmethod
    def get_database_path():
        return DB_PATH

    @staticmethod
    def get_seed_counts() -> dict[str, int]:
        return get_seed_counts()
