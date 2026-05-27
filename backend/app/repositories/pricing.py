"""Repository for pricing calculations and reference data."""
from app.database import calculate_pricing, get_pricing_defaults, list_repair_categories, update_pricing_defaults


class PricingRepository:
    """Handles pricing calculation and rule data access."""

    @staticmethod
    def calculate(payload: dict) -> dict:
        return calculate_pricing(payload)

    @staticmethod
    def list_repair_categories() -> list[dict]:
        return list_repair_categories()

    @staticmethod
    def get_defaults() -> dict:
        return get_pricing_defaults()

    @staticmethod
    def update_defaults(payload: dict) -> dict:
        return update_pricing_defaults(payload)
