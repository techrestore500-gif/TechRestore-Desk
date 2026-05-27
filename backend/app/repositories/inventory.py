"""Repository for inventory and donor device data access."""
from app.database import (
    create_inventory_movement,
    create_inventory_reconciliation,
    create_inventory_purchase,
    create_donor,
    create_part,
    delete_part,
    get_connection,
    get_donor,
    get_inventory_purchase,
    get_low_stock_parts,
    get_part,
    get_part_usage_for_repair_action,
    get_part_usage_history,
    harvest_part_from_donor,
    list_inventory_movements,
    list_inventory_reconciliations,
    list_inventory_purchases,
    list_donors,
    list_parts,
    log_part_usage,
    update_donor,
    update_part,
)


class InventoryRepository:
    """Handles inventory and donor database operations."""

    @staticmethod
    def list_parts(category: str | None = None, status: str | None = None, low_stock_only: bool = False) -> list[dict]:
        return list_parts(category=category, status=status, low_stock_only=low_stock_only)

    @staticmethod
    def get_part(part_id: int) -> dict | None:
        return get_part(part_id)

    @staticmethod
    def repair_action_exists(repair_action_id: int) -> bool:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT id FROM repair_actions WHERE id = ?",
                (repair_action_id,),
            ).fetchone()
        return row is not None

    @staticmethod
    def create_part(payload: dict) -> dict:
        return create_part(payload)

    @staticmethod
    def update_part(part_id: int, payload: dict) -> dict | None:
        return update_part(part_id, payload)

    @staticmethod
    def delete_part(part_id: int) -> bool:
        return delete_part(part_id)

    @staticmethod
    def log_part_usage(repair_action_id: int, part_id: int, quantity_used: int = 1) -> dict:
        return log_part_usage(repair_action_id, part_id, quantity_used)

    @staticmethod
    def get_part_usage_for_repair_action(repair_action_id: int) -> list[dict]:
        return get_part_usage_for_repair_action(repair_action_id)

    @staticmethod
    def get_part_usage_history(part_id: int) -> list[dict]:
        return get_part_usage_history(part_id)

    @staticmethod
    def list_donors(status: str | None = None, device_model: str | None = None) -> list[dict]:
        return list_donors(status=status, device_model=device_model)

    @staticmethod
    def get_donor(donor_id: int) -> dict | None:
        return get_donor(donor_id)

    @staticmethod
    def create_donor(payload: dict) -> dict:
        return create_donor(payload)

    @staticmethod
    def update_donor(donor_id: int, payload: dict) -> dict | None:
        return update_donor(donor_id, payload)

    @staticmethod
    def harvest_part_from_donor(donor_id: int, part_id: int) -> dict | None:
        return harvest_part_from_donor(donor_id, part_id)

    @staticmethod
    def get_low_stock_parts() -> list[dict]:
        return get_low_stock_parts()

    @staticmethod
    def create_movement(
        *,
        movement_type: str,
        quantity: int,
        part_id: int | None = None,
        donor_id: int | None = None,
        reason: str | None = None,
        ticket_id: int | None = None,
        repair_action_id: int | None = None,
        actor_user_id: int | None = None,
        request_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        return create_inventory_movement(
            movement_type=movement_type,
            quantity=quantity,
            part_id=part_id,
            donor_id=donor_id,
            reason=reason,
            ticket_id=ticket_id,
            repair_action_id=repair_action_id,
            actor_user_id=actor_user_id,
            request_id=request_id,
            metadata=metadata,
        )

    @staticmethod
    def list_movements(
        *,
        page: int = 1,
        page_size: int = 50,
        part_id: int | None = None,
        movement_type: str | None = None,
    ) -> dict:
        return list_inventory_movements(
            page=page,
            page_size=page_size,
            part_id=part_id,
            movement_type=movement_type,
        )

    @staticmethod
    def create_reconciliation(
        *,
        part_id: int,
        expected_quantity: int,
        actual_quantity: int,
        reason: str,
        resolved_by: str | None,
    ) -> dict:
        return create_inventory_reconciliation(
            part_id=part_id,
            expected_quantity=expected_quantity,
            actual_quantity=actual_quantity,
            reason=reason,
            resolved_by=resolved_by,
        )

    @staticmethod
    def list_reconciliations(part_id: int | None = None) -> list[dict]:
        return list_inventory_reconciliations(part_id=part_id)

    @staticmethod
    def list_purchases() -> list[dict]:
        return list_inventory_purchases()

    @staticmethod
    def get_purchase(purchase_id: int) -> dict | None:
        return get_inventory_purchase(purchase_id)

    @staticmethod
    def create_purchase(payload: dict) -> dict:
        return create_inventory_purchase(payload)
