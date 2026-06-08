from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

import yfinance as yf

logger = logging.getLogger(__name__)

SYMBOL_DISPLAY_NAME = {
    "^GSPC": "S&P 500",
    "^IXIC": "Nasdaq",
    "^DJI": "Dow Jones",
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
}


@dataclass(frozen=True)
class MarketQuote:
    display_name: str
    symbol: str
    latest_price: float | None
    daily_change: float | None
    daily_percent_change: float | None
    source_time: str | None
    available: bool = True


def _display_name_for_symbol(symbol: str) -> str:
    return SYMBOL_DISPLAY_NAME.get(symbol, symbol)


def _format_source_time(raw_value: object) -> str | None:
    if raw_value is None:
        return None

    if isinstance(raw_value, datetime):
        return raw_value.isoformat()

    to_pydatetime = getattr(raw_value, "to_pydatetime", None)
    if callable(to_pydatetime):
        try:
            dt_value = to_pydatetime()
            if isinstance(dt_value, datetime):
                return dt_value.isoformat()
        except Exception:
            logger.debug("Failed converting provider timestamp", exc_info=True)

    return str(raw_value)


def _fetch_quote_from_yfinance(symbol: str) -> MarketQuote:
    ticker = yf.Ticker(symbol)
    history = ticker.history(period="2d", interval="1d", auto_adjust=False)

    if history.empty or "Close" not in history:
        raise RuntimeError(f"No market history returned for symbol {symbol}")

    close_series = history["Close"].dropna()
    if close_series.empty:
        raise RuntimeError(f"No close data returned for symbol {symbol}")

    latest_price = float(close_series.iloc[-1])

    if len(close_series) > 1:
        previous_close = float(close_series.iloc[-2])
    else:
        open_series = history["Open"].dropna() if "Open" in history else None
        previous_close = float(open_series.iloc[-1]) if open_series is not None and not open_series.empty else latest_price

    daily_change = latest_price - previous_close
    daily_percent_change = 0.0 if previous_close == 0 else (daily_change / previous_close) * 100.0

    source_time: str | None = None
    if len(history.index) > 0:
        source_time = _format_source_time(history.index[-1])

    return MarketQuote(
        display_name=_display_name_for_symbol(symbol),
        symbol=symbol,
        latest_price=latest_price,
        daily_change=daily_change,
        daily_percent_change=daily_percent_change,
        source_time=source_time,
        available=True,
    )


def fetch_market_data(symbols: list[str], provider: str = "yfinance") -> list[MarketQuote]:
    provider_name = provider.strip().lower()
    if provider_name != "yfinance":
        raise ValueError(f"Unsupported market data provider: {provider}")

    quotes: list[MarketQuote] = []
    for symbol in symbols:
        try:
            quote = _fetch_quote_from_yfinance(symbol)
            quotes.append(quote)
        except Exception as exc:
            logger.exception("Market data fetch failed for symbol=%s", symbol)
            quotes.append(
                MarketQuote(
                    display_name=_display_name_for_symbol(symbol),
                    symbol=symbol,
                    latest_price=None,
                    daily_change=None,
                    daily_percent_change=None,
                    source_time=None,
                    available=False,
                )
            )
            logger.debug("Market data provider error for symbol=%s: %s", symbol, exc)

    return quotes
