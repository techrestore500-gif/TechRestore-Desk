"""Repository for repair category reference data management."""
from __future__ import annotations
from app.database import (
    create_repair_category,
    list_repair_categories_for_management,
    update_repair_category,
)


class RepairCategoryRepository:
    """Handles CRUD operations for repair categories."""

    @staticmethod
    def list(include_inactive: bool = False) -> list[dict]:
        return list_repair_categories_for_management(include_inactive=include_inactive)

    @staticmethod
    def create(payload: dict) -> dict:
        return create_repair_category(payload)

    @staticmethod
    def update(repair_category_id: int, payload: dict) -> dict | None:
        return update_repair_category(repair_category_id, payload)
