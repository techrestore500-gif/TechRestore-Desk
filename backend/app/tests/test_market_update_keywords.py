from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.database as database
from app.main import app
from market_updates.keyword_handlers import handle_inbound_market_sms
from market_updates.notifications import create_notification, list_notifications_for_recipient


@pytest.fixture
def market_updates_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "market_updates.sqlite"
    monkeypatch.setenv("MARKET_UPDATES_DB_PATH", str(db_path))
    return db_path


@pytest.fixture
def quote_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    class Quote:
        def __init__(self, display_name: str):
            self.display_name = display_name
            self.symbol = "BTC-USD"
            self.latest_price = 67250.0
            self.daily_change = 730.0
            self.daily_percent_change = 1.1
            self.source_time = "2026-06-07T14:00:00"
            self.available = True

    def fake_fetch(symbols, provider="yfinance"):
        display = "Bitcoin"
        symbol = symbols[0]
        if symbol == "^GSPC":
            display = "S&P 500"
        elif symbol == "^IXIC":
            display = "Nasdaq Composite"
        elif symbol == "BTC-USD":
            display = "Bitcoin"

        quote = Quote(display)
        quote.symbol = symbol
        return [quote]

    monkeypatch.setattr("market_updates.keyword_handlers.fetch_market_data", fake_fetch)


@pytest.fixture
def client_auth(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, market_updates_db: Path) -> TestClient:
    test_db_path = tmp_path / "tech_restore_desk_auth_test.sqlite"
    test_backups_dir = tmp_path / "backups"
    test_backups_dir.mkdir()
    test_activity_log_path = tmp_path / "system_activity_log.json"

    monkeypatch.setattr(database, "DB_PATH", test_db_path)
    monkeypatch.setattr(database, "DEFAULT_DB_PATH", test_db_path)
    monkeypatch.setattr(database, "LEGACY_DB_PATH", test_db_path)
    monkeypatch.setattr(database, "BACKUPS_DIR", test_backups_dir)
    monkeypatch.setattr(database, "SYSTEM_ACTIVITY_LOG_PATH", test_activity_log_path)

    monkeypatch.setenv("REPAIR_DESK_AUTH_ENABLED", "1")
    monkeypatch.setenv("TECH_RESTORE_AUTH_BYPASS", "0")

    database.initialize_database()

    with TestClient(app) as test_client:
        yield test_client


def test_help_shows_main_menu(market_updates_db: Path) -> None:
    reply = handle_inbound_market_sms(from_number="+15555550001", body="HELP")
    assert "Market Assistant:" in reply
    assert "CHECK - check prices" in reply


def test_check_then_btc_returns_status(quote_stub: None, market_updates_db: Path) -> None:
    first = handle_inbound_market_sms(from_number="+15555550001", body="CHECK")
    assert "What do you want to check?" in first

    second = handle_inbound_market_sms(from_number="+15555550001", body="BTC")
    assert "Bitcoin is at" in second
    assert "Reply CHECK" in second


def test_check_more_and_custom_prompts(quote_stub: None, market_updates_db: Path) -> None:
    handle_inbound_market_sms(from_number="+15555550001", body="CHECK")
    more = handle_inbound_market_sms(from_number="+15555550001", body="MORE")
    assert "More choices:" in more

    custom = handle_inbound_market_sms(from_number="+15555550001", body="CUSTOM")
    assert "Reply with a ticker symbol" in custom


def test_remind_price_flow_to_draft_and_save(market_updates_db: Path) -> None:
    assert "What kind of notification" in handle_inbound_market_sms(from_number="+15555550001", body="REMIND")
    assert "Which market" in handle_inbound_market_sms(from_number="+15555550001", body="PRICE")
    assert "selected" in handle_inbound_market_sms(from_number="+15555550001", body="BTC")
    assert "What price" in handle_inbound_market_sms(from_number="+15555550001", body="BELOW")

    draft = handle_inbound_market_sms(from_number="+15555550001", body="60000")
    assert "Alert draft:" in draft

    saved = handle_inbound_market_sms(from_number="+15555550001", body="SAVE")
    assert "Saved." in saved


def test_delete_cancels_draft(market_updates_db: Path) -> None:
    handle_inbound_market_sms(from_number="+15555550001", body="REMIND")
    handle_inbound_market_sms(from_number="+15555550001", body="PRICE")
    handle_inbound_market_sms(from_number="+15555550001", body="BTC")
    handle_inbound_market_sms(from_number="+15555550001", body="BELOW")
    handle_inbound_market_sms(from_number="+15555550001", body="60000")

    deleted = handle_inbound_market_sms(from_number="+15555550001", body="DELETE")
    assert "Draft deleted" in deleted


def test_time_and_daily_flows_create_drafts(market_updates_db: Path) -> None:
    handle_inbound_market_sms(from_number="+15555550001", body="REMIND")
    handle_inbound_market_sms(from_number="+15555550001", body="TIME")
    ask_time = handle_inbound_market_sms(from_number="+15555550001", body="STATUS")
    assert "What time should I send it" in ask_time
    draft_time = handle_inbound_market_sms(from_number="+15555550001", body="9:30 AM")
    assert "Reminder draft:" in draft_time

    handle_inbound_market_sms(from_number="+15555550001", body="CANCEL")

    handle_inbound_market_sms(from_number="+15555550001", body="REMIND")
    handle_inbound_market_sms(from_number="+15555550001", body="DAILY")
    ask_daily_time = handle_inbound_market_sms(from_number="+15555550001", body="BTC")
    assert "What daily time" in ask_daily_time
    draft_daily = handle_inbound_market_sms(from_number="+15555550001", body="10:00")
    assert "Reminder draft:" in draft_daily


def test_list_only_shows_sender_notifications_and_actions(market_updates_db: Path) -> None:
    create_notification(
        recipient_phone="+15555550001",
        notification_type="price_alert",
        symbol="BTC-USD",
        display_name="Bitcoin",
        condition="below",
        threshold=60000,
        reminder_time=None,
        recurrence=None,
        original_text="Bitcoin below",
    )
    create_notification(
        recipient_phone="+15555559999",
        notification_type="price_alert",
        symbol="ETH-USD",
        display_name="Ethereum",
        condition="above",
        threshold=4000,
        reminder_time=None,
        recurrence=None,
        original_text="Ethereum above",
    )

    listed = handle_inbound_market_sms(from_number="+15555550001", body="LIST")
    assert "Your notifications:" in listed
    assert "Bitcoin" in listed
    assert "Ethereum" not in listed

    paused = handle_inbound_market_sms(from_number="+15555550001", body="PAUSE 1")
    assert "Paused" in paused

    resumed = handle_inbound_market_sms(from_number="+15555550001", body="RESUME 1")
    assert "Resumed" in resumed

    deleted = handle_inbound_market_sms(from_number="+15555550001", body="DELETE 1")
    assert "Deleted" in deleted


def test_stop_clears_setup_and_unknown_shows_next_options(market_updates_db: Path) -> None:
    handle_inbound_market_sms(from_number="+15555550001", body="CHECK")
    unknown = handle_inbound_market_sms(from_number="+15555550001", body="WAT")
    assert "Unknown symbol" in unknown

    canceled = handle_inbound_market_sms(from_number="+15555550001", body="STOP")
    assert "Canceled" in canceled


def test_market_updates_sms_webhook_returns_twiml_public_route(client_auth: TestClient, quote_stub: None) -> None:
    response = client_auth.post(
        "/api/market-updates/sms",
        data={"From": "+15555550001", "Body": "HELP", "MessageSid": "SM123"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "<Message>" in response.text
    assert "Market Assistant:" in response.text
