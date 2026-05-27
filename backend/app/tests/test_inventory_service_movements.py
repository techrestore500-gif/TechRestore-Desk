import pytest

from app.repositories.inventory import InventoryRepository
from app.services.inventory import InventoryService


def test_adjust_part_stock_rejects_invalid_movement_type(monkeypatch):
    with pytest.raises(ValueError, match="Invalid movement type"):
        InventoryService.adjust_part_stock(
            part_id=1,
            quantity_delta=1,
            movement_type="add",
            reason="invalid path",
        )


def test_adjust_part_stock_rejects_negative_result(monkeypatch):
    monkeypatch.setattr(InventoryRepository, "get_part", lambda _part_id: {"id": 1, "quantity_on_hand": 1, "reorder_level": 0})

    with pytest.raises(ValueError, match="cannot be negative"):
        InventoryService.adjust_part_stock(
            part_id=1,
            quantity_delta=-3,
            movement_type="correction",
            reason="count mismatch",
        )


def test_reconcile_stock_without_adjustment_only_records(monkeypatch):
    monkeypatch.setattr(InventoryRepository, "get_part", lambda _part_id: {"id": 9, "quantity_on_hand": 5, "reorder_level": 2})
    monkeypatch.setattr(
        InventoryRepository,
        "create_reconciliation",
        lambda **kwargs: {
            "id": 1,
            "part_id": kwargs["part_id"],
            "expected_quantity": kwargs["expected_quantity"],
            "actual_quantity": kwargs["actual_quantity"],
            "discrepancy": kwargs["actual_quantity"] - kwargs["expected_quantity"],
            "reason": kwargs["reason"],
            "resolved_by": kwargs["resolved_by"],
            "created_at": "2026-05-10T00:00:00+00:00",
        },
    )

    called = {"adjust": False}

    def fake_adjust(**_kwargs):
        called["adjust"] = True

    monkeypatch.setattr(InventoryService, "adjust_part_stock", fake_adjust)

    record = InventoryService.reconcile_stock(
        part_id=9,
        actual_quantity=3,
        reason="manual cycle count",
        apply_adjustment=False,
        resolved_by="Ops",
    )

    assert record["part_id"] == 9
    assert record["discrepancy"] == -2
    assert called["adjust"] is False


def test_reconcile_stock_with_adjustment_applies_correction(monkeypatch):
    monkeypatch.setattr(InventoryRepository, "get_part", lambda _part_id: {"id": 11, "quantity_on_hand": 4, "reorder_level": 2})
    monkeypatch.setattr(
        InventoryRepository,
        "create_reconciliation",
        lambda **kwargs: {
            "id": 2,
            "part_id": kwargs["part_id"],
            "expected_quantity": kwargs["expected_quantity"],
            "actual_quantity": kwargs["actual_quantity"],
            "discrepancy": kwargs["actual_quantity"] - kwargs["expected_quantity"],
            "reason": kwargs["reason"],
            "resolved_by": kwargs["resolved_by"],
            "created_at": "2026-05-10T00:00:00+00:00",
        },
    )

    called = {"delta": None, "movement_type": None}

    def fake_adjust(**kwargs):
        called["delta"] = kwargs["quantity_delta"]
        called["movement_type"] = kwargs["movement_type"]
        return {"id": kwargs["part_id"], "quantity_on_hand": 8, "reorder_level": 2}

    monkeypatch.setattr(InventoryService, "adjust_part_stock", fake_adjust)

    record = InventoryService.reconcile_stock(
        part_id=11,
        actual_quantity=8,
        reason="bin recount",
        apply_adjustment=True,
        resolved_by="Ops",
    )

    assert record["discrepancy"] == 4
    assert called["delta"] == 4
    assert called["movement_type"] == "correction"
