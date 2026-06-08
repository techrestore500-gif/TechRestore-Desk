from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from market_updates.notifications import create_notification, get_notification_by_id
from market_updates.notification_runner import run


@pytest.fixture
def market_updates_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "market_updates.sqlite"
    monkeypatch.setenv("MARKET_UPDATES_DB_PATH", str(db_path))
    return db_path


@pytest.fixture
def base_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC_TEST")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_PHONE_NUMBER", "+15555550001")
    monkeypatch.setenv("MARKET_UPDATE_TO_NUMBER", "+15555550002")


def test_price_alert_triggers_when_condition_met(
    market_updates_db: Path,
    base_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_notification(
        recipient_phone="+15555550002",
        notification_type="price_alert",
        symbol="BTC-USD",
        display_name="Bitcoin",
        condition="below",
        threshold=60000,
        reminder_time=None,
        recurrence=None,
        original_text="Bitcoin below 60000",
    )

    class Quote:
        available = True
        latest_price = 59000.0

    monkeypatch.setattr("market_updates.notification_runner.fetch_market_data", lambda symbols, provider="yfinance": [Quote()])

    sent: list[dict] = []

    class Result:
        success = True
        message_sid = "SM_TEST"
        error_message = None

    def fake_send(**kwargs):
        sent.append(kwargs)
        return Result()

    monkeypatch.setattr("market_updates.notification_runner.send_market_update_sms", fake_send)

    exit_code = run([])
    assert exit_code == 0
    assert len(sent) == 1


def test_price_alert_does_not_trigger_when_condition_not_met(
    market_updates_db: Path,
    base_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_notification(
        recipient_phone="+15555550002",
        notification_type="price_alert",
        symbol="BTC-USD",
        display_name="Bitcoin",
        condition="below",
        threshold=60000,
        reminder_time=None,
        recurrence=None,
        original_text="Bitcoin below 60000",
    )

    class Quote:
        available = True
        latest_price = 62000.0

    monkeypatch.setattr("market_updates.notification_runner.fetch_market_data", lambda symbols, provider="yfinance": [Quote()])

    sent: list[dict] = []

    class Result:
        success = True
        message_sid = "SM_TEST"
        error_message = None

    def fake_send(**kwargs):
        sent.append(kwargs)
        return Result()

    monkeypatch.setattr("market_updates.notification_runner.send_market_update_sms", fake_send)

    exit_code = run([])
    assert exit_code == 0
    assert len(sent) == 0


def test_one_time_reminder_sends_once(
    market_updates_db: Path,
    base_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reminder = create_notification(
        recipient_phone="+15555550002",
        notification_type="one_time_reminder",
        symbol=None,
        display_name="Market status",
        condition=None,
        threshold=None,
        reminder_time="2026-06-07T10:00:00",
        recurrence="once",
        original_text="Check markets",
    )

    monkeypatch.setattr("market_updates.notification_runner._now_local", lambda: datetime.fromisoformat("2026-06-07T10:05:00"))
    monkeypatch.setattr("market_updates.notification_runner.fetch_market_data", lambda symbols, provider="yfinance": [])

    sent: list[dict] = []

    class Result:
        success = True
        message_sid = "SM_TEST"
        error_message = None

    def fake_send(**kwargs):
        sent.append(kwargs)
        return Result()

    monkeypatch.setattr("market_updates.notification_runner.send_market_update_sms", fake_send)

    assert run([]) == 0
    assert run([]) == 0
    assert len(sent) == 1

    refreshed = get_notification_by_id(int(reminder["id"]))
    assert refreshed is not None
    assert int(refreshed["completed"]) == 1


def test_daily_reminder_advances_after_send(
    market_updates_db: Path,
    base_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reminder = create_notification(
        recipient_phone="+15555550002",
        notification_type="daily_reminder",
        symbol=None,
        display_name="Market status",
        condition=None,
        threshold=None,
        reminder_time="09:30",
        recurrence="daily",
        original_text="Daily status",
    )

    monkeypatch.setattr("market_updates.notification_runner._now_local", lambda: datetime.fromisoformat("2026-06-07T09:35:00"))
    monkeypatch.setattr("market_updates.notification_runner.fetch_market_data", lambda symbols, provider="yfinance": [])

    sent: list[dict] = []

    class Result:
        success = True
        message_sid = "SM_TEST"
        error_message = None

    def fake_send(**kwargs):
        sent.append(kwargs)
        return Result()

    monkeypatch.setattr("market_updates.notification_runner.send_market_update_sms", fake_send)

    assert run([]) == 0
    assert run([]) == 0
    assert len(sent) == 1

    refreshed = get_notification_by_id(int(reminder["id"]))
    assert refreshed is not None
    assert refreshed["last_triggered_at"] is not None


def test_runner_dry_run_sends_no_messages(
    market_updates_db: Path,
    base_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_notification(
        recipient_phone="+15555550002",
        notification_type="price_alert",
        symbol="BTC-USD",
        display_name="Bitcoin",
        condition="below",
        threshold=60000,
        reminder_time=None,
        recurrence=None,
        original_text="Bitcoin below 60000",
    )

    class Quote:
        available = True
        latest_price = 59000.0

    monkeypatch.setattr("market_updates.notification_runner.fetch_market_data", lambda symbols, provider="yfinance": [Quote()])

    sent: list[dict] = []

    class Result:
        success = True
        message_sid = "SM_TEST"
        error_message = None

    def fake_send(**kwargs):
        sent.append(kwargs)
        return Result()

    monkeypatch.setattr("market_updates.notification_runner.send_market_update_sms", fake_send)

    exit_code = run(["--dry-run"])
    assert exit_code == 0
    assert sent == []
