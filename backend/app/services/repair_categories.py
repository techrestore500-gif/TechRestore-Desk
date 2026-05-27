"""Service layer for repair category management."""
from app.repositories.repair_categories import RepairCategoryRepository


class RepairCategoryService:
    """Business logic for repair category settings workflows."""

    @staticmethod
    def list_categories(include_inactive: bool = False) -> list[dict]:
        return RepairCategoryRepository.list(include_inactive=include_inactive)

    @staticmethod
    def create_category(payload: dict) -> dict:
        return RepairCategoryRepository.create(payload)

    @staticmethod
    def update_category(repair_category_id: int, payload: dict) -> dict | None:
        return RepairCategoryRepository.update(repair_category_id, payload)
