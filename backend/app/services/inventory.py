"""Service layer for inventory and donor workflows."""
from app.core.request_context import get_actor, get_request_id
from app.events.audit_events import donor_harvested, inventory_mutation
from app.events.dispatcher import event_dispatcher
from app.events.types import DonorHarvestedEvent, InventoryLowEvent
from app.repositories.inventory import InventoryRepository
from app.services.audit import AuditService


class InventoryService:
    """Business logic for inventory operations."""

    @staticmethod
    def _record_movement(
        *,
        movement_type: str,
        quantity: int,
        part_id: int | None = None,
        donor_id: int | None = None,
        reason: str | None = None,
        ticket_id: int | None = None,
        repair_action_id: int | None = None,
        metadata: dict | None = None,
    ) -> dict:
        actor = get_actor() or {}
        actor_user_id = actor.get("id") if isinstance(actor.get("id"), int) else None
        return InventoryRepository.create_movement(
            movement_type=movement_type,
            quantity=quantity,
            part_id=part_id,
            donor_id=donor_id,
            reason=reason,
            ticket_id=ticket_id,
            repair_action_id=repair_action_id,
            actor_user_id=actor_user_id,
            request_id=get_request_id(),
            metadata=metadata,
        )

    @staticmethod
    def _publish_low_stock_if_needed(part: dict | None) -> None:
        if not part:
            return
        if int(part["quantity_on_hand"]) <= int(part["reorder_level"]):
            event_dispatcher.publish(
                InventoryLowEvent(
                    part_id=int(part["id"]),
                    quantity_on_hand=int(part["quantity_on_hand"]),
                    reorder_level=int(part["reorder_level"]),
                )
            )

    @staticmethod
    def list_parts(category: str | None = None, status: str | None = None, low_stock_only: bool = False) -> list[dict]:
        return InventoryRepository.list_parts(category=category, status=status, low_stock_only=low_stock_only)

    @staticmethod
    def get_part(part_id: int) -> dict | None:
        return InventoryRepository.get_part(part_id)

    @staticmethod
    def create_part(payload: dict) -> dict:
        created = InventoryRepository.create_part(payload)
        initial_quantity = int(created.get("quantity_on_hand", 0))
        if initial_quantity > 0:
            InventoryService._record_movement(
                movement_type="add",
                quantity=initial_quantity,
                part_id=int(created["id"]),
                reason="Initial stock",
            )
        InventoryService._publish_low_stock_if_needed(created)
        return created

    @staticmethod
    def update_part(part_id: int, payload: dict) -> dict | None:
        before = InventoryRepository.get_part(part_id)
        updated = InventoryRepository.update_part(part_id, payload)
        if before is None or updated is None:
            return updated

        before_qty = int(before.get("quantity_on_hand", 0))
        after_qty = int(updated.get("quantity_on_hand", 0))
        delta = after_qty - before_qty
        if delta != 0:
            InventoryService._record_movement(
                movement_type="adjust",
                quantity=delta,
                part_id=part_id,
                reason=payload.get("adjustment_reason") or "Stock adjusted",
            )
            InventoryService._publish_low_stock_if_needed(updated)

        return updated

    @staticmethod
    def delete_part(part_id: int) -> bool:
        return InventoryRepository.delete_part(part_id)

    @staticmethod
    def log_part_usage(repair_action_id: int, part_id: int, quantity_used: int = 1) -> dict:
        # Gate 1 migration note: keep request/business validations in service.
        if quantity_used <= 0:
            raise ValueError("Quantity used must be greater than zero")
        before_part = InventoryRepository.get_part(part_id)
        if before_part is None:
            raise ValueError("Part not found")
        if not InventoryRepository.repair_action_exists(repair_action_id):
            raise ValueError("Repair action not found")
        usage = InventoryRepository.log_part_usage(repair_action_id, part_id, quantity_used)
        after_part = InventoryRepository.get_part(part_id)

        InventoryService._record_movement(
            movement_type="consume",
            quantity=-int(quantity_used),
            part_id=part_id,
            reason="Part used in repair action",
            repair_action_id=repair_action_id,
            ticket_id=usage.get("ticket_id"),
            metadata={"usage_id": usage.get("id")},
        )

        AuditService.log_event(
            inventory_mutation(
                part_id=part_id,
                action="inventory_part_usage_logged",
                old_value=before_part,
                new_value={"usage": usage, "part": after_part},
            )
        )

        InventoryService._publish_low_stock_if_needed(after_part)
        return usage

    @staticmethod
    def get_part_usage_for_repair_action(repair_action_id: int) -> list[dict]:
        return InventoryRepository.get_part_usage_for_repair_action(repair_action_id)

    @staticmethod
    def get_part_usage_history(part_id: int) -> list[dict]:
        return InventoryRepository.get_part_usage_history(part_id)

    @staticmethod
    def list_donors(status: str | None = None, device_model: str | None = None) -> list[dict]:
        return InventoryRepository.list_donors(status=status, device_model=device_model)

    @staticmethod
    def get_donor(donor_id: int) -> dict | None:
        return InventoryRepository.get_donor(donor_id)

    @staticmethod
    def create_donor(payload: dict) -> dict:
        return InventoryRepository.create_donor(payload)

    @staticmethod
    def update_donor(donor_id: int, payload: dict) -> dict | None:
        return InventoryRepository.update_donor(donor_id, payload)

    @staticmethod
    def harvest_part_from_donor(donor_id: int, part_id: int) -> dict | None:
        # Gate 1 migration note: guardrails remain in service for future auth/audit hooks.
        donor_before = InventoryRepository.get_donor(donor_id)
        if donor_before is None:
            return None
        part_before = InventoryRepository.get_part(part_id)
        if part_before is None:
            raise ValueError("Part not found")

        donor_after = InventoryRepository.harvest_part_from_donor(donor_id, part_id)
        if donor_after is not None:
            part_after = InventoryRepository.update_part(
                part_id,
                {"quantity_on_hand": int(part_before.get("quantity_on_hand", 0)) + 1},
            )
            InventoryService._record_movement(
                movement_type="donor_harvest",
                quantity=1,
                part_id=part_id,
                donor_id=donor_id,
                reason="Part harvested from donor device",
                metadata={"donor_status": donor_after.get("status")},
            )
            AuditService.log_event(
                donor_harvested(
                    donor_id=donor_id,
                    part_id=part_id,
                    old_value=donor_before,
                    new_value={"donor": donor_after, "part": part_after},
                )
            )
            InventoryService._publish_low_stock_if_needed(part_after)
            event_dispatcher.publish(DonorHarvestedEvent(donor_id=donor_id, part_id=part_id))
        return donor_after

    @staticmethod
    def adjust_part_stock(
        *,
        part_id: int,
        quantity_delta: int,
        movement_type: str,
        reason: str,
        ticket_id: int | None = None,
    ) -> dict:
        if movement_type not in {"adjust", "transfer", "return", "correction"}:
            raise ValueError("Invalid movement type for manual adjustment")
        if quantity_delta == 0:
            raise ValueError("Quantity delta cannot be zero")

        part = InventoryRepository.get_part(part_id)
        if part is None:
            raise ValueError("Part not found")

        next_quantity = int(part["quantity_on_hand"]) + int(quantity_delta)
        if next_quantity < 0:
            raise ValueError("Stock cannot be negative")

        updated = InventoryRepository.update_part(part_id, {"quantity_on_hand": next_quantity})
        if updated is None:
            raise ValueError("Part not found")

        InventoryService._record_movement(
            movement_type=movement_type,
            quantity=int(quantity_delta),
            part_id=part_id,
            reason=reason,
            ticket_id=ticket_id,
        )
        InventoryService._publish_low_stock_if_needed(updated)
        return updated

    @staticmethod
    def list_movements(
        *,
        page: int = 1,
        page_size: int = 50,
        part_id: int | None = None,
        movement_type: str | None = None,
    ) -> dict:
        return InventoryRepository.list_movements(
            page=page,
            page_size=page_size,
            part_id=part_id,
            movement_type=movement_type,
        )

    @staticmethod
    def reconcile_stock(
        *,
        part_id: int,
        actual_quantity: int,
        reason: str,
        apply_adjustment: bool,
        resolved_by: str | None,
    ) -> dict:
        part = InventoryRepository.get_part(part_id)
        if part is None:
            raise ValueError("Part not found")

        expected_quantity = int(part["quantity_on_hand"])
        record = InventoryRepository.create_reconciliation(
            part_id=part_id,
            expected_quantity=expected_quantity,
            actual_quantity=int(actual_quantity),
            reason=reason,
            resolved_by=resolved_by,
        )

        discrepancy = int(record["discrepancy"])
        if apply_adjustment and discrepancy != 0:
            InventoryService.adjust_part_stock(
                part_id=part_id,
                quantity_delta=discrepancy,
                movement_type="correction",
                reason=f"reconciliation:{reason}",
            )

        return record

    @staticmethod
    def list_reconciliations(part_id: int | None = None) -> list[dict]:
        return InventoryRepository.list_reconciliations(part_id=part_id)

    @staticmethod
    def get_low_stock_parts() -> list[dict]:
        return InventoryRepository.get_low_stock_parts()

    @staticmethod
    def list_purchases() -> list[dict]:
        return InventoryRepository.list_purchases()

    @staticmethod
    def get_purchase(purchase_id: int) -> dict | None:
        return InventoryRepository.get_purchase(purchase_id)

    @staticmethod
    def create_purchase(payload: dict) -> dict:
        if not payload.get("items"):
            raise ValueError("At least one purchase line item is required")
        return InventoryRepository.create_purchase(payload)
