from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AuditLogEvent:
    entity_type: str
    action: str
    entity_id: int | None = None
    old_value: Any = None
    new_value: Any = None
    user_id: int | None = None
    request_id: str | None = None


def ticket_status_changed(ticket_id: int, old_status: str, new_status: str, note: str | None) -> AuditLogEvent:
    return AuditLogEvent(
        entity_type="ticket",
        entity_id=ticket_id,
        action="ticket_status_changed",
        old_value={"status": old_status},
        new_value={"status": new_status, "note": note},
    )


def ticket_closed(ticket_id: int, old_status: str, final_price: float | None, note: str | None) -> AuditLogEvent:
    return AuditLogEvent(
        entity_type="ticket",
        entity_id=ticket_id,
        action="ticket_closed",
        old_value={"status": old_status},
        new_value={"status": "Picked Up / Closed", "final_price": final_price, "note": note},
    )


def inventory_mutation(part_id: int, action: str, old_value: dict | None, new_value: dict | None) -> AuditLogEvent:
    return AuditLogEvent(
        entity_type="inventory_part",
        entity_id=part_id,
        action=action,
        old_value=old_value,
        new_value=new_value,
    )


def donor_harvested(donor_id: int, part_id: int, old_value: dict | None, new_value: dict | None) -> AuditLogEvent:
    return AuditLogEvent(
        entity_type="donor_device",
        entity_id=donor_id,
        action="donor_part_harvested",
        old_value=old_value,
        new_value={"part_id": part_id, "donor": new_value},
    )


def loaner_activity(loaner_id: int, action: str, old_value: dict | None, new_value: dict | None) -> AuditLogEvent:
    return AuditLogEvent(
        entity_type="loaner_phone",
        entity_id=loaner_id,
        action=action,
        old_value=old_value,
        new_value=new_value,
    )


def pricing_modified(old_value: dict | None, new_value: dict | None) -> AuditLogEvent:
    return AuditLogEvent(
        entity_type="pricing_defaults",
        entity_id=1,
        action="pricing_rules_updated",
        old_value=old_value,
        new_value=new_value,
    )


def technician_assignment_changed(ticket_id: int, old_value: str | None, new_value: str | None) -> AuditLogEvent:
    return AuditLogEvent(
        entity_type="ticket",
        entity_id=ticket_id,
        action="technician_assignment_changed",
        old_value={"assigned_technician": old_value},
        new_value={"assigned_technician": new_value},
    )


def admin_action(entity_type: str, entity_id: int | None, action: str, old_value: dict | None, new_value: dict | None) -> AuditLogEvent:
    return AuditLogEvent(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        old_value=old_value,
        new_value=new_value,
    )
