import pytest

from app.repositories.inventory import InventoryRepository
from app.repositories.loaner import LoanerRepository
from app.repositories.queue import QueueRepository
from app.services.inventory import InventoryService
from app.services.loaner import LoanerService
from app.services.pricing import PricingService
from app.services.queue import QueueService


def test_inventory_log_part_usage_requires_positive_quantity(monkeypatch):
    with pytest.raises(ValueError, match="greater than zero"):
        InventoryService.log_part_usage(repair_action_id=1, part_id=1, quantity_used=0)


def test_inventory_log_part_usage_requires_part_and_repair_action(monkeypatch):
    monkeypatch.setattr(InventoryRepository, "get_part", lambda part_id: None)
    with pytest.raises(ValueError, match="Part not found"):
        InventoryService.log_part_usage(repair_action_id=1, part_id=9, quantity_used=1)

    monkeypatch.setattr(InventoryRepository, "get_part", lambda part_id: {"id": part_id})
    monkeypatch.setattr(InventoryRepository, "repair_action_exists", lambda repair_action_id: False)
    with pytest.raises(ValueError, match="Repair action not found"):
        InventoryService.log_part_usage(repair_action_id=9, part_id=1, quantity_used=1)


def test_inventory_harvest_returns_none_when_donor_missing(monkeypatch):
    monkeypatch.setattr(InventoryRepository, "get_donor", lambda donor_id: None)
    result = InventoryService.harvest_part_from_donor(3, 4)
    assert result is None


def test_inventory_harvest_requires_part(monkeypatch):
    monkeypatch.setattr(InventoryRepository, "get_donor", lambda donor_id: {"id": donor_id})
    monkeypatch.setattr(InventoryRepository, "get_part", lambda part_id: None)
    with pytest.raises(ValueError, match="Part not found"):
        InventoryService.harvest_part_from_donor(3, 4)


def test_loaner_checkout_requires_customer_and_ticket(monkeypatch):
    monkeypatch.setattr(LoanerRepository, "customer_exists", lambda customer_id: False)
    with pytest.raises(ValueError, match="Customer does not exist"):
        LoanerService.checkout_loaner(1, {"customer_id": 1, "ticket_id": 2})

    monkeypatch.setattr(LoanerRepository, "customer_exists", lambda customer_id: True)
    monkeypatch.setattr(LoanerRepository, "ticket_exists", lambda ticket_id: False)
    with pytest.raises(ValueError, match="Ticket does not exist"):
        LoanerService.checkout_loaner(1, {"customer_id": 1, "ticket_id": 2})


def test_queue_assignment_normalizes_empty_technician(monkeypatch):
    calls = {}

    def fake_assign(ticket_id: int, assigned_technician: str | None):
        calls["ticket_id"] = ticket_id
        calls["assigned_technician"] = assigned_technician
        return {"ticket_id": ticket_id, "assigned_technician": assigned_technician, "updated": True}

    monkeypatch.setattr(QueueRepository, "assign_ticket", fake_assign)

    result = QueueService.assign_ticket(ticket_id=7, assigned_technician="   ")

    assert result == {"ticket_id": 7, "assigned_technician": None, "updated": True}
    assert calls == {"ticket_id": 7, "assigned_technician": None}


def test_pricing_update_rules_rejects_negative_defaults():
    with pytest.raises(ValueError, match="Labor rate cannot be negative"):
        PricingService.update_rules({"base_labor_rate_per_hour": -1})

    with pytest.raises(ValueError, match="Diagnostic fee cannot be negative"):
        PricingService.update_rules({"diagnostic_fee": -5})
