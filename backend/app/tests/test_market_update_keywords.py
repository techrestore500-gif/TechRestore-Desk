from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.database as database
from app.main import app
from market_updates.allowlist import is_number_allowed, upsert_allowlist_number
from market_updates.feedback_store import list_feedback_entries
from market_updates.keyword_handlers import handle_inbound_market_sms
from market_updates.notifications import create_notification, list_notifications_for_recipient


@pytest.fixture
def market_updates_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "market_updates.sqlite"
    monkeypatch.setenv("MARKET_UPDATES_DB_PATH", str(db_path))
    monkeypatch.setenv("MARKET_ACCESS_APPROVER_NUMBER", "+18483291230")
    monkeypatch.delenv("MARKET_UPDATES_ALLOWED_NUMBERS", raising=False)
    upsert_allowlist_number("+15555550001", label="Primary tester", enabled=True)
    upsert_allowlist_number("+15555559999", label="Secondary tester", enabled=True)
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
        out = []
        for symbol in symbols:
            display = "Bitcoin"
            if symbol == "^GSPC":
                display = "S&P 500"
            elif symbol == "^IXIC":
                display = "Nasdaq Composite"
            elif symbol == "BTC-USD":
                display = "Bitcoin"
            elif symbol == "AAPL":
                display = "Apple"

            quote = Quote(display)
            quote.symbol = symbol
            out.append(quote)
        return out

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
    assert "DATECHECK" in reply
    assert "TICKER/LOOKUP/FIND" in reply


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
    assert "What date and time should I send it" in ask_time
    draft_time = handle_inbound_market_sms(from_number="+15555550001", body="2026-06-20 9:30 AM")
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
        stop_time=None,
        recurrence=None,
        interval_minutes=None,
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
        stop_time=None,
        recurrence=None,
        interval_minutes=None,
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


def test_blocked_number_receives_request_prompt(market_updates_db: Path) -> None:
    reply = handle_inbound_market_sms(from_number="+15550001111", body="HELP")
    assert "tech restore" in reply.lower()
    assert "market" not in reply.lower()
    assert "please call us instead of texting" in reply.lower()
    assert "8483291230" in reply


def test_blocked_number_can_submit_invite_request(market_updates_db: Path) -> None:
    reply = handle_inbound_market_sms(from_number="+15550001111", body="REQUEST Alex")
    assert "pending approval" in reply


def test_at_market_request_notifies_approver(market_updates_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeConfig:
        twilio_account_sid = "AC_TEST"
        twilio_auth_token = "token"
        twilio_from_number = "+15555550001"

    sent: list[dict] = []

    class SendResult:
        success = True
        message_sid = "SM_TEST"
        error_message = None

    def fake_send_market_update_sms(**kwargs):
        sent.append(kwargs)
        return SendResult()

    monkeypatch.setattr("market_updates.keyword_handlers.load_config", lambda: FakeConfig())
    monkeypatch.setattr("market_updates.keyword_handlers.send_market_update_sms", fake_send_market_update_sms)

    reply = handle_inbound_market_sms(from_number="+15550001111", body="@market")
    assert "request #" in reply.lower()
    assert sent
    assert sent[0]["to_number"] == "+18483291230"


def test_approver_yes_adds_requester_to_allowlist(market_updates_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeConfig:
        twilio_account_sid = "AC_TEST"
        twilio_auth_token = "token"
        twilio_from_number = "+15555550001"

    class SendResult:
        success = True
        message_sid = "SM_TEST"
        error_message = None

    monkeypatch.setattr("market_updates.keyword_handlers.load_config", lambda: FakeConfig())
    monkeypatch.setattr("market_updates.keyword_handlers.send_market_update_sms", lambda **kwargs: SendResult())

    requester = "+15550001111"
    initial = handle_inbound_market_sms(from_number=requester, body="@market")
    assert "request #" in initial.lower()

    approve = handle_inbound_market_sms(from_number="+18483291230", body="YES 1")
    assert "approved request" in approve.lower()
    assert is_number_allowed(requester) is True


def test_feedback_keyword_persists_feedback(market_updates_db: Path) -> None:
    reply = handle_inbound_market_sms(from_number="+15555550001", body="FEEDBACK add option chain view")
    assert "queued for review" in reply

    entries = list_feedback_entries(limit=10)
    assert entries
    assert "option chain" in entries[0]["feedback_text"]


def test_check_list_fetches_multiple_symbols(quote_stub: None, market_updates_db: Path) -> None:
    reply = handle_inbound_market_sms(from_number="+15555550001", body="CHECK BTC AAPL")
    assert "Latest prices:" in reply
    assert "Bitcoin:" in reply
    assert "Apple:" in reply


def test_ticker_lookup_keyword_returns_matches(market_updates_db: Path) -> None:
    reply = handle_inbound_market_sms(from_number="+15555550001", body="TICKER apple")
    assert "Ticker matches:" in reply
    assert "AAPL" in reply


def test_datecheck_keyword_returns_historical_values(market_updates_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class HistoricalQuote:
        def __init__(self, symbol: str, display_name: str):
            self.symbol = symbol
            self.display_name = display_name
            self.target_date = "2026-06-01"
            self.close_price = 123.45
            self.source_time = "2026-06-01T16:00:00+00:00"
            self.available = True

    def fake_hist_fetch(symbols, target_date, provider="yfinance"):
        out = []
        for symbol in symbols:
            display = "Bitcoin" if symbol == "BTC-USD" else symbol
            out.append(HistoricalQuote(symbol, display))
        return out

    monkeypatch.setattr("market_updates.keyword_handlers.fetch_market_data_for_date", fake_hist_fetch)

    reply = handle_inbound_market_sms(from_number="+15555550001", body="DATECHECK 2026-06-01 BTC")
    assert "Close on 2026-06-01:" in reply
    assert "Bitcoin:" in reply
