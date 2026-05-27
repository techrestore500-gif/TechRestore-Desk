import pytest

from app.services.ticket import TicketService
from app.repositories.ticket import TicketRepository


def test_close_ticket_returns_none_when_ticket_missing(monkeypatch):
    monkeypatch.setattr(TicketRepository, "get", lambda ticket_id: None)

    result = TicketService.close_ticket(999, {"changed_by": "Alex"})

    assert result is None


def test_close_ticket_rejects_active_loaner(monkeypatch):
    monkeypatch.setattr(TicketRepository, "get", lambda ticket_id: {"id": ticket_id, "status": "Ready for Pickup", "final_price": 99.0})
    monkeypatch.setattr(TicketRepository, "has_active_loaner_checkout", lambda ticket_id: True)

    with pytest.raises(ValueError, match="loaner is still checked out"):
        TicketService.close_ticket(7, {"changed_by": "Alex"})


def test_close_ticket_calls_repository_with_expected_values(monkeypatch):
    calls = {}

    monkeypatch.setattr(
        TicketRepository,
        "get",
        lambda ticket_id: {
            "id": ticket_id,
            "status": "Ready for Pickup",
            "final_price": 129.0,
        },
    )
    monkeypatch.setattr(TicketRepository, "has_active_loaner_checkout", lambda ticket_id: False)

    def fake_close(ticket_id, *, old_status, final_price, changed_by, close_note):
        calls["ticket_id"] = ticket_id
        calls["old_status"] = old_status
        calls["final_price"] = final_price
        calls["changed_by"] = changed_by
        calls["close_note"] = close_note

    monkeypatch.setattr(TicketRepository, "close_ticket", fake_close)

    result = TicketService.close_ticket(7, {"changed_by": "Alex"})

    assert result == {
        "ticket_id": 7,
        "status": "Picked Up / Closed",
        "closed": True,
    }
    assert calls == {
        "ticket_id": 7,
        "old_status": "Ready for Pickup",
        "final_price": 129.0,
        "changed_by": "Alex",
        "close_note": "Ticket closed",
    }
