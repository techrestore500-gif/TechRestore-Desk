from __future__ import annotations

from app.database import list_overdue_loaner_checkouts
from app.events.dispatcher import event_dispatcher
from app.events.types import LoanerOverdueEvent
from app.services.audit import AuditService


def send_ready_for_pickup_notification(payload: dict) -> None:
    ticket_id = int(payload["ticket_id"])
    AuditService.log(
        entity_type="ticket",
        entity_id=ticket_id,
        action="job_ready_for_pickup_notification_enqueued",
        new_value={"ticket_id": ticket_id},
    )


def send_low_inventory_alert(payload: dict) -> None:
    part_id = int(payload["part_id"])
    AuditService.log(
        entity_type="inventory_part",
        entity_id=part_id,
        action="job_low_inventory_alert_enqueued",
        new_value=payload,
    )


def send_loaner_overdue_notification(payload: dict) -> None:
    checkout_id = int(payload["checkout_id"])
    AuditService.log(
        entity_type="loaner_checkout",
        entity_id=checkout_id,
        action="job_loaner_overdue_notification_enqueued",
        new_value=payload,
    )


def generate_daily_report(payload: dict) -> None:
    AuditService.log(
        entity_type="report",
        action="job_daily_report_enqueued",
        new_value=payload,
    )


def scan_overdue_loaners(_: dict) -> None:
    overdue = list_overdue_loaner_checkouts()
    for item in overdue:
        event_dispatcher.publish(
            LoanerOverdueEvent(
                checkout_id=item["id"],
                loaner_phone_id=item["loaner_phone_id"],
                ticket_id=item["ticket_id"],
            )
        )
