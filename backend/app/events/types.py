from __future__ import annotations

from dataclasses import dataclass, field

from app.database import utc_now


@dataclass(frozen=True)
class DomainEvent:
    occurred_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class TicketCreatedEvent(DomainEvent):
    ticket_id: int = 0
    customer_id: int = 0


@dataclass(frozen=True)
class TicketClosedEvent(DomainEvent):
    ticket_id: int = 0
    final_price: float | None = None


@dataclass(frozen=True)
class InventoryLowEvent(DomainEvent):
    part_id: int = 0
    quantity_on_hand: int = 0
    reorder_level: int = 0


@dataclass(frozen=True)
class DonorHarvestedEvent(DomainEvent):
    donor_id: int = 0
    part_id: int = 0


@dataclass(frozen=True)
class LoanerOverdueEvent(DomainEvent):
    checkout_id: int = 0
    loaner_phone_id: int = 0
    ticket_id: int = 0


@dataclass(frozen=True)
class PricingApprovedEvent(DomainEvent):
    updated_fields: list[str] = field(default_factory=list)
