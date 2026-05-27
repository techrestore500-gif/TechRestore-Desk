from __future__ import annotations

from app.events.dispatcher import event_dispatcher
from app.events.types import InventoryLowEvent, LoanerOverdueEvent, PricingApprovedEvent, TicketClosedEvent
from app.jobs.queue import JobPriority, job_queue

_registered = False


def _on_ticket_closed(event: TicketClosedEvent) -> None:
    job_queue.enqueue(
        job_name="send_ready_for_pickup_notification",
        payload={"ticket_id": event.ticket_id},
        queue=JobPriority.CRITICAL,
        idempotency_key=f"ticket-closed-notify:{event.ticket_id}",
    )


def _on_inventory_low(event: InventoryLowEvent) -> None:
    job_queue.enqueue(
        job_name="send_low_inventory_alert",
        payload={
            "part_id": event.part_id,
            "quantity_on_hand": event.quantity_on_hand,
            "reorder_level": event.reorder_level,
        },
        queue=JobPriority.DEFAULT,
        idempotency_key=f"inventory-low:{event.part_id}:{event.quantity_on_hand}",
    )


def _on_loaner_overdue(event: LoanerOverdueEvent) -> None:
    job_queue.enqueue(
        job_name="send_loaner_overdue_notification",
        payload={
            "checkout_id": event.checkout_id,
            "loaner_phone_id": event.loaner_phone_id,
            "ticket_id": event.ticket_id,
        },
        queue=JobPriority.DEFAULT,
        idempotency_key=f"loaner-overdue:{event.checkout_id}",
    )


def _on_pricing_approved(event: PricingApprovedEvent) -> None:
    job_queue.enqueue(
        job_name="generate_daily_report",
        payload={"trigger": "pricing_update", "updated_fields": event.updated_fields},
        queue=JobPriority.LOW,
    )


def register_event_subscribers() -> None:
    global _registered
    if _registered:
        return

    event_dispatcher.subscribe(TicketClosedEvent, _on_ticket_closed)
    event_dispatcher.subscribe(InventoryLowEvent, _on_inventory_low)
    event_dispatcher.subscribe(LoanerOverdueEvent, _on_loaner_overdue)
    event_dispatcher.subscribe(PricingApprovedEvent, _on_pricing_approved)
    _registered = True
