"""Service layer for pricing workflows."""
from app.events.audit_events import pricing_modified
from app.events.dispatcher import event_dispatcher
from app.events.types import PricingApprovedEvent
from app.repositories.pricing import PricingRepository
from app.services.audit import AuditService


class PricingService:
    """Business logic for pricing workflows."""

    @staticmethod
    def calculate(payload: dict) -> dict:
        return PricingRepository.calculate(payload)

    @staticmethod
    def get_rules() -> dict:
        return {
            "defaults": PricingRepository.get_defaults(),
            "difficulty_multipliers": {
                "1": 1.00,
                "2": 1.15,
                "3": 1.30,
                "4": 1.50,
                "5": 1.75,
            },
            "risk_multipliers": {
                "1": 1.00,
                "2": 1.10,
                "3": 1.20,
                "4": 1.35,
                "5": 1.50,
            },
            "repair_categories": PricingRepository.list_repair_categories(),
        }

    @staticmethod
    def update_rules(payload: dict) -> dict:
        # Gate 1 migration note: keep write-side business validation in service.
        # This preserves repository as a pure data access layer and keeps route thin.
        base_rate = payload.get("base_labor_rate_per_hour")
        diagnostic_fee = payload.get("diagnostic_fee")
        if base_rate is not None and base_rate < 0:
            raise ValueError("Labor rate cannot be negative")
        if diagnostic_fee is not None and diagnostic_fee < 0:
            raise ValueError("Diagnostic fee cannot be negative")
        previous_defaults = PricingRepository.get_defaults()
        updated_defaults = PricingRepository.update_defaults(payload)

        AuditService.log_event(pricing_modified(old_value=previous_defaults, new_value=updated_defaults))
        event_dispatcher.publish(PricingApprovedEvent(updated_fields=sorted(payload.keys())))
        return updated_defaults
