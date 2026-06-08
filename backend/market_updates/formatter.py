from __future__ import annotations

from datetime import datetime

from market_updates.market_data import MarketQuote


def _is_crypto_symbol(symbol: str) -> bool:
    return symbol.endswith("-USD")


def _format_price(symbol: str, price: float) -> str:
    if _is_crypto_symbol(symbol):
        return f"${price:,.2f}"
    return f"{price:,.2f}"


def _format_percent_change(value: float) -> str:
    return f"{value:+.2f}%"


def _format_as_of_time(raw_source_time: str | None, now: datetime | None = None) -> str:
    if raw_source_time:
        try:
            parsed = datetime.fromisoformat(raw_source_time.replace("Z", "+00:00"))
            return parsed.strftime("%I:%M %p").lstrip("0")
        except ValueError:
            pass

    fallback = now or datetime.now()
    return fallback.strftime("%I:%M %p").lstrip("0")


def format_market_update_sms(quotes: list[MarketQuote], now: datetime | None = None) -> str:
    lines = ["Market Update:"]

    first_source_time: str | None = None
    for quote in quotes:
        if first_source_time is None and quote.source_time:
            first_source_time = quote.source_time

        if not quote.available or quote.latest_price is None or quote.daily_percent_change is None:
            lines.append(f"{quote.display_name}: unavailable")
            continue

        price_text = _format_price(quote.symbol, quote.latest_price)
        percent_text = _format_percent_change(quote.daily_percent_change)
        lines.append(f"{quote.display_name}: {price_text} ({percent_text})")

    lines.append(f"As of {_format_as_of_time(first_source_time, now=now)}")
    return "\n".join(lines)
