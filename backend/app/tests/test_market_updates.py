from __future__ import annotations

from datetime import date, datetime

import pytest

from market_updates.config import MarketUpdateConfig, load_config
from market_updates.formatter import format_market_update_sms
from market_updates.market_data import HistoricalMarketQuote, MarketQuote, fetch_market_data, fetch_market_data_for_date
from market_updates.sms_sender import send_market_update_sms_to_many
from market_updates.send_market_update import run


def test_load_config_raises_on_missing_required_environment_variables() -> None:
    with pytest.raises(ValueError) as excinfo:
        load_config(env={})

    error_text = str(excinfo.value)
    assert "TWILIO_ACCOUNT_SID" in error_text
    assert "TWILIO_AUTH_TOKEN" in error_text
    assert "TWILIO_FROM_NUMBER" in error_text


def test_load_config_prefers_market_update_to_numbers() -> None:
    config = load_config(
        env={
            "TWILIO_ACCOUNT_SID": "AC_TEST",
            "TWILIO_AUTH_TOKEN": "token",
            "TWILIO_FROM_NUMBER": "+15555550001",
            "MARKET_UPDATE_TO_NUMBER": "+15555550002",
            "MARKET_UPDATE_TO_NUMBERS": "+18483291230,+19296529336",
        }
    )

    assert config.to_numbers == ["+18483291230", "+19296529336"]


def test_load_config_falls_back_to_single_market_update_to_number() -> None:
    config = load_config(
        env={
            "TWILIO_ACCOUNT_SID": "AC_TEST",
            "TWILIO_AUTH_TOKEN": "token",
            "TWILIO_FROM_NUMBER": "+15555550001",
            "MARKET_UPDATE_TO_NUMBER": "+15555550002",
        }
    )

    assert config.to_numbers == ["+15555550002"]


def test_load_config_uses_twilio_phone_number_as_from_number_fallback() -> None:
    config = load_config(
        env={
            "TWILIO_ACCOUNT_SID": "AC_TEST",
            "TWILIO_AUTH_TOKEN": "token",
            "TWILIO_PHONE_NUMBER": "+15555550001",
            "MARKET_UPDATE_TO_NUMBER": "+15555550002",
        }
    )

    assert config.twilio_from_number == "+15555550001"


def test_formatter_outputs_compact_sms_lines() -> None:
    quotes = [
        MarketQuote(
            display_name="S&P 500",
            symbol="^GSPC",
            latest_price=5432.1,
            daily_change=22.6,
            daily_percent_change=0.42,
            source_time="2026-06-07T16:05:00",
            available=True,
        ),
        MarketQuote(
            display_name="Bitcoin",
            symbol="BTC-USD",
            latest_price=67250.0,
            daily_change=730.0,
            daily_percent_change=1.1,
            source_time="2026-06-07T16:05:00",
            available=True,
        ),
        MarketQuote(
            display_name="Nasdaq",
            symbol="^IXIC",
            latest_price=None,
            daily_change=None,
            daily_percent_change=None,
            source_time=None,
            available=False,
        ),
    ]

    message = format_market_update_sms(quotes, now=datetime(2026, 6, 7, 16, 5, 0))

    assert "Market Update:" in message
    assert "S&P 500: 5,432.10 (+0.42%)" in message
    assert "Bitcoin: $67,250.00 (+1.10%)" in message
    assert "Nasdaq: unavailable" in message
    assert "As of 4:05 PM" in message


def test_fetch_market_data_handles_partial_symbol_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_chart_fetch(symbol: str) -> MarketQuote:
        if symbol == "BTC-USD":
            raise RuntimeError("Provider timeout")
        return MarketQuote(
            display_name="S&P 500",
            symbol=symbol,
            latest_price=5432.1,
            daily_change=22.6,
            daily_percent_change=0.42,
            source_time="2026-06-07T16:05:00",
            available=True,
        )

    def fake_yfinance_fetch(symbol: str) -> MarketQuote:
        if symbol == "BTC-USD":
            raise RuntimeError("Provider timeout")
        return MarketQuote(
            display_name="S&P 500",
            symbol=symbol,
            latest_price=5432.1,
            daily_change=22.6,
            daily_percent_change=0.42,
            source_time="2026-06-07T16:05:00",
            available=True,
        )

    monkeypatch.setattr("market_updates.market_data._fetch_quote_from_yahoo_chart", fake_chart_fetch)
    monkeypatch.setattr("market_updates.market_data._fetch_quote_from_yfinance", fake_yfinance_fetch)

    quotes = fetch_market_data(["^GSPC", "BTC-USD"], provider="yfinance")
    assert len(quotes) == 2

    first, second = quotes
    assert first.available is True
    assert first.latest_price == 5432.1

    assert second.available is False
    assert second.display_name == "Bitcoin"
    assert second.latest_price is None


def test_fetch_market_data_for_date_handles_partial_symbol_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_hist_fetch(symbol: str, target_date: date) -> HistoricalMarketQuote:
        if symbol == "BTC-USD":
            raise RuntimeError("Provider timeout")
        return HistoricalMarketQuote(
            display_name="S&P 500",
            symbol=symbol,
            target_date=target_date.isoformat(),
            close_price=5300.0,
            source_time="2026-06-01T21:00:00+00:00",
            available=True,
        )

    monkeypatch.setattr("market_updates.market_data._fetch_historical_close_from_yahoo_chart", fake_hist_fetch)

    quotes = fetch_market_data_for_date(["^GSPC", "BTC-USD"], date(2026, 6, 1), provider="yfinance")
    assert len(quotes) == 2

    first, second = quotes
    assert first.available is True
    assert first.close_price == 5300.0

    assert second.available is False
    assert second.display_name == "Bitcoin"
    assert second.close_price is None


def test_cli_dry_run_does_not_send_sms(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    config = MarketUpdateConfig(
        twilio_account_sid="AC_TEST",
        twilio_auth_token="token",
        twilio_from_number="+15555550001",
        to_numbers=["+15555550002", "+15555550003"],
        symbols=["^GSPC", "BTC-USD"],
        provider="yfinance",
    )

    monkeypatch.setattr("market_updates.send_market_update.load_config", lambda: config)
    monkeypatch.setattr(
        "market_updates.send_market_update.fetch_market_data",
        lambda symbols, provider: [
            MarketQuote(
                display_name="S&P 500",
                symbol="^GSPC",
                latest_price=5432.1,
                daily_change=22.6,
                daily_percent_change=0.42,
                source_time="2026-06-07T16:05:00",
                available=True,
            )
        ],
    )
    monkeypatch.setattr("market_updates.send_market_update.format_market_update_sms", lambda quotes: "Market Update:\nS&P 500: 5,432.10 (+0.42%)")

    def fail_send(**kwargs):
        raise AssertionError("SMS send should not be called during dry run")

    monkeypatch.setattr("market_updates.send_market_update.send_market_update_sms_to_many", fail_send)

    exit_code = run(["--dry-run"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Market Update:" in output
    assert "Would send to: +15555550002, +15555550003" in output
    assert "Dry run complete. SMS not sent." in output


def test_cli_to_override_accepts_comma_separated_list(monkeypatch: pytest.MonkeyPatch) -> None:
    config = MarketUpdateConfig(
        twilio_account_sid="AC_TEST",
        twilio_auth_token="token",
        twilio_from_number="+15555550001",
        to_numbers=["+15555550002"],
        symbols=["^GSPC"],
        provider="yfinance",
    )

    monkeypatch.setattr("market_updates.send_market_update.load_config", lambda: config)
    monkeypatch.setattr(
        "market_updates.send_market_update.fetch_market_data",
        lambda symbols, provider: [
            MarketQuote(
                display_name="S&P 500",
                symbol="^GSPC",
                latest_price=5432.1,
                daily_change=22.6,
                daily_percent_change=0.42,
                source_time="2026-06-07T16:05:00",
                available=True,
            )
        ],
    )
    monkeypatch.setattr("market_updates.send_market_update.format_market_update_sms", lambda quotes: "ok")

    captured: dict[str, object] = {}

    class FakeResult:
        def __init__(self, to_number: str):
            self.to_number = to_number
            self.success = True
            self.message_sid = "SM_TEST"
            self.error_message = None

    def fake_send_market_update_sms_to_many(**kwargs):
        captured.update(kwargs)
        return [FakeResult(number) for number in kwargs["to_numbers"]]

    monkeypatch.setattr(
        "market_updates.send_market_update.send_market_update_sms_to_many",
        fake_send_market_update_sms_to_many,
    )

    exit_code = run(["--to", "+18483291230,+19296529336"])

    assert exit_code == 0
    assert captured["to_numbers"] == ["+18483291230", "+19296529336"]


def test_send_market_update_sms_to_many_continues_when_one_recipient_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeMessages:
        def create(self, *, body: str, from_: str, to: str):
            if to == "+19296529336":
                raise RuntimeError("Twilio test failure")

            class Response:
                sid = "SM_OK"
                status = "queued"

            return Response()

    class FakeClient:
        def __init__(self, *_args, **_kwargs):
            self.messages = FakeMessages()

    monkeypatch.setattr("market_updates.sms_sender.Client", FakeClient)

    results = send_market_update_sms_to_many(
        twilio_account_sid="AC_TEST",
        twilio_auth_token="token",
        from_number="+15555550001",
        to_numbers=["+18483291230", "+19296529336"],
        message_body="Market Update",
    )

    assert len(results) == 2
    assert results[0].to_number == "+18483291230"
    assert results[0].success is True
    assert results[0].message_sid == "SM_OK"

    assert results[1].to_number == "+19296529336"
    assert results[1].success is False
    assert results[1].message_sid is None
    assert "Twilio test failure" in (results[1].error_message or "")


def test_send_at_rejects_time_that_already_passed_today(monkeypatch: pytest.MonkeyPatch) -> None:
    config = MarketUpdateConfig(
        twilio_account_sid="AC_TEST",
        twilio_auth_token="token",
        twilio_from_number="+15555550001",
        to_numbers=["+18483291230", "+19296529336"],
        symbols=["^GSPC"],
        provider="yfinance",
    )

    monkeypatch.setattr("market_updates.send_market_update.load_config", lambda: config)
    monkeypatch.setattr(
        "market_updates.send_market_update.fetch_market_data",
        lambda symbols, provider: [
            MarketQuote(
                display_name="S&P 500",
                symbol="^GSPC",
                latest_price=5432.1,
                daily_change=22.6,
                daily_percent_change=0.42,
                source_time="2026-06-07T16:05:00",
                available=True,
            )
        ],
    )
    monkeypatch.setattr("market_updates.send_market_update.format_market_update_sms", lambda quotes: "ok")
    monkeypatch.setattr("market_updates.send_market_update._now_local", lambda: datetime(2026, 6, 7, 15, 0, 0))

    def fail_sleep(_seconds: float) -> None:
        raise AssertionError("Sleep should not be called when send-at time already passed")

    monkeypatch.setattr("market_updates.send_market_update.time.sleep", fail_sleep)

    exit_code = run(["--send-at", "14:00"])
    assert exit_code == 1
