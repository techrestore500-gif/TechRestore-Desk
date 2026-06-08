from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import requests
import yfinance as yf
from requests import Session
import urllib3

logger = logging.getLogger(__name__)

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
_REQUEST_SESSION = Session()
_REQUEST_SESSION.headers.update({"User-Agent": "Mozilla/5.0"})
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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


@dataclass(frozen=True)
class HistoricalMarketQuote:
    display_name: str
    symbol: str
    target_date: str
    close_price: float | None
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


def _coerce_float(raw_value: object) -> float | None:
    if raw_value is None:
        return None

    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return None


def _fetch_quote_from_yahoo_chart(symbol: str) -> MarketQuote:
    response = _REQUEST_SESSION.get(
        YAHOO_CHART_URL.format(symbol=symbol),
        params={"range": "2d", "interval": "1d", "includePrePost": "false", "events": "div,splits"},
        timeout=20,
        verify=False,
    )
    response.raise_for_status()

    payload = response.json()
    chart = payload.get("chart") or {}
    results = chart.get("result") or []
    if not results:
        raise RuntimeError(f"No chart result returned for symbol {symbol}")

    result = results[0]
    meta = result.get("meta") or {}
    indicators = result.get("indicators") or {}
    quote_series = indicators.get("quote") or []
    if not quote_series:
        raise RuntimeError(f"No quote series returned for symbol {symbol}")

    price_series = quote_series[0]
    close_values = [float(value) for value in (price_series.get("close") or []) if value is not None]
    if not close_values:
        raise RuntimeError(f"No close data returned for symbol {symbol}")

    latest_price = _coerce_float(meta.get("regularMarketPrice")) or close_values[-1]
    previous_close = (
        _coerce_float(meta.get("chartPreviousClose"))
        or _coerce_float(meta.get("regularMarketPreviousClose"))
        or (close_values[-2] if len(close_values) > 1 else None)
        or _coerce_float(price_series.get("open"))
        or latest_price
    )
    daily_change = latest_price - previous_close
    daily_percent_change = 0.0 if previous_close == 0 else (daily_change / previous_close) * 100.0

    source_time: str | None = None
    market_time = _coerce_float(meta.get("regularMarketTime"))
    if market_time is not None:
        source_time = datetime.fromtimestamp(int(market_time), tz=ZoneInfo("UTC")).isoformat()
    else:
        timestamps = result.get("timestamp") or []
        if timestamps:
            source_time = datetime.fromtimestamp(int(timestamps[-1]), tz=ZoneInfo("UTC")).isoformat()

    return MarketQuote(
        display_name=_display_name_for_symbol(symbol),
        symbol=symbol,
        latest_price=latest_price,
        daily_change=daily_change,
        daily_percent_change=daily_percent_change,
        source_time=source_time,
        available=True,
    )


def _fetch_historical_close_from_yahoo_chart(symbol: str, target_date: date) -> HistoricalMarketQuote:
    period_start = datetime.combine(target_date - timedelta(days=7), time(0, 0), tzinfo=ZoneInfo("UTC"))
    period_end = datetime.combine(target_date + timedelta(days=1), time(0, 0), tzinfo=ZoneInfo("UTC"))

    response = _REQUEST_SESSION.get(
        YAHOO_CHART_URL.format(symbol=symbol),
        params={
            "period1": int(period_start.timestamp()),
            "period2": int(period_end.timestamp()),
            "interval": "1d",
            "includePrePost": "false",
            "events": "div,splits",
        },
        timeout=20,
        verify=False,
    )
    response.raise_for_status()

    payload = response.json()
    chart = payload.get("chart") or {}
    results = chart.get("result") or []
    if not results:
        raise RuntimeError(f"No chart result returned for symbol {symbol}")

    result = results[0]
    timestamps = result.get("timestamp") or []
    indicators = result.get("indicators") or {}
    quote_series = indicators.get("quote") or []
    if not timestamps or not quote_series:
        raise RuntimeError(f"No historical data returned for symbol {symbol}")

    closes = quote_series[0].get("close") or []
    close_candidates: list[tuple[datetime, float]] = []
    for ts, raw_close in zip(timestamps, closes):
        close_value = _coerce_float(raw_close)
        if close_value is None:
            continue
        ts_dt = datetime.fromtimestamp(int(ts), tz=ZoneInfo("UTC"))
        if ts_dt.date() <= target_date:
            close_candidates.append((ts_dt, close_value))

    if not close_candidates:
        raise RuntimeError(f"No historical close on or before {target_date.isoformat()} for symbol {symbol}")

    source_time, close_price = close_candidates[-1]
    return HistoricalMarketQuote(
        display_name=_display_name_for_symbol(symbol),
        symbol=symbol,
        target_date=target_date.isoformat(),
        close_price=close_price,
        source_time=source_time.isoformat(),
        available=True,
    )


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
            quote = _fetch_quote_from_yahoo_chart(symbol)
            if quote.latest_price is None or quote.daily_percent_change is None:
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


def fetch_market_data_for_date(symbols: list[str], target_date: date, provider: str = "yfinance") -> list[HistoricalMarketQuote]:
    provider_name = provider.strip().lower()
    if provider_name != "yfinance":
        raise ValueError(f"Unsupported market data provider: {provider}")

    quotes: list[HistoricalMarketQuote] = []
    for symbol in symbols:
        try:
            quote = _fetch_historical_close_from_yahoo_chart(symbol, target_date)
            quotes.append(quote)
        except Exception as exc:
            logger.exception("Historical market data fetch failed for symbol=%s date=%s", symbol, target_date.isoformat())
            quotes.append(
                HistoricalMarketQuote(
                    display_name=_display_name_for_symbol(symbol),
                    symbol=symbol,
                    target_date=target_date.isoformat(),
                    close_price=None,
                    source_time=None,
                    available=False,
                )
            )
            logger.debug("Historical provider error for symbol=%s date=%s: %s", symbol, target_date.isoformat(), exc)

    return quotes
