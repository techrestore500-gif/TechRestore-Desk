from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SymbolChoice:
    symbol: str
    display_name: str


@dataclass(frozen=True)
class TickerProfile:
    symbol: str
    display_name: str
    description: str
    keywords: tuple[str, ...]


SYMBOL_ALIASES: dict[str, SymbolChoice] = {
    "BTC": SymbolChoice("BTC-USD", "Bitcoin"),
    "BITCOIN": SymbolChoice("BTC-USD", "Bitcoin"),
    "ETH": SymbolChoice("ETH-USD", "Ethereum"),
    "SPX": SymbolChoice("^GSPC", "S&P 500"),
    "GSPC": SymbolChoice("^GSPC", "S&P 500"),
    "NASDAQ": SymbolChoice("^IXIC", "Nasdaq Composite"),
    "IXIC": SymbolChoice("^IXIC", "Nasdaq Composite"),
    "DOW": SymbolChoice("^DJI", "Dow Jones"),
    "DJI": SymbolChoice("^DJI", "Dow Jones"),
    "SPY": SymbolChoice("SPY", "SPY ETF"),
    "QQQ": SymbolChoice("QQQ", "QQQ ETF"),
    "AAPL": SymbolChoice("AAPL", "Apple"),
    "TSLA": SymbolChoice("TSLA", "Tesla"),
    "NVDA": SymbolChoice("NVDA", "Nvidia"),
}

TOP_LEVEL_KEYWORDS = {
    "HELP",
    "MENU",
    "CHECK",
    "DATECHECK",
    "TICKER",
    "LOOKUP",
    "FIND",
    "FEEDBACK",
    "REMIND",
    "LIST",
    "NOTIFICATIONS",
    "ALERTS",
    "STOP",
    "CANCEL",
}

REMINDER_TYPE_KEYWORDS = {"PRICE", "TIME", "DAILY", "UPDATE", "INTERVAL"}
DIRECTION_KEYWORDS = {"ABOVE", "BELOW"}
CONFIRM_KEYWORDS = {"SAVE", "YES", "CONFIRM", "EDIT", "DELETE", "STOP", "CANCEL"}

TICKER_PROFILES: tuple[TickerProfile, ...] = (
    TickerProfile("AAPL", "Apple", "Consumer technology company (iPhone, Mac, services).", ("APPLE", "IPHONE", "MAC")),
    TickerProfile("MSFT", "Microsoft", "Software and cloud platform company.", ("MICROSOFT", "AZURE", "WINDOWS")),
    TickerProfile("NVDA", "Nvidia", "Semiconductor and AI computing company.", ("NVIDIA", "GPU", "AI CHIP")),
    TickerProfile("TSLA", "Tesla", "Electric vehicles and energy systems.", ("TESLA", "EV")),
    TickerProfile("AMZN", "Amazon", "E-commerce and AWS cloud platform.", ("AMAZON", "AWS")),
    TickerProfile("META", "Meta", "Social and advertising platform company.", ("META", "FACEBOOK", "INSTAGRAM")),
    TickerProfile("GOOGL", "Alphabet", "Search and advertising company (Google).", ("GOOGLE", "ALPHABET", "YOUTUBE")),
    TickerProfile("SPY", "SPY ETF", "ETF that tracks the S&P 500 index.", ("SPY", "SP500 ETF", "S&P ETF")),
    TickerProfile("QQQ", "QQQ ETF", "ETF that tracks the Nasdaq-100 index.", ("QQQ", "NASDAQ ETF")),
    TickerProfile("BTC-USD", "Bitcoin", "Bitcoin spot USD market price.", ("BITCOIN", "BTC", "CRYPTO")),
    TickerProfile("ETH-USD", "Ethereum", "Ethereum spot USD market price.", ("ETHEREUM", "ETH", "CRYPTO")),
    TickerProfile("^GSPC", "S&P 500", "S&P 500 index level.", ("SPX", "S&P", "S&P 500", "GSPC")),
    TickerProfile("^IXIC", "Nasdaq Composite", "Nasdaq Composite index level.", ("NASDAQ", "IXIC", "NASDAQ COMPOSITE")),
    TickerProfile("^DJI", "Dow Jones", "Dow Jones Industrial Average index level.", ("DOW", "DJI", "DOW JONES")),
)


def normalize_message(body: str | None) -> str:
    if body is None:
        return ""
    compact = re.sub(r"\s+", " ", body).strip()
    return compact.upper()


def parse_symbol_keyword(message: str) -> SymbolChoice | None:
    return SYMBOL_ALIASES.get(message)


def parse_list_action(message: str) -> tuple[str, int] | None:
    match = re.match(r"^(DELETE|PAUSE|RESUME)\s+(\d+)$", message)
    if not match:
        return None
    return match.group(1), int(match.group(2))


def parse_check_symbols(message: str) -> list[SymbolChoice]:
    compact = normalize_message(message)
    if not compact.startswith("CHECK "):
        return []

    raw_tokens = compact.split(" ")[1:]
    if not raw_tokens:
        return []

    choices: list[SymbolChoice] = []
    seen_symbols: set[str] = set()
    for raw in raw_tokens:
        token = re.sub(r"[^A-Z0-9\-\^]", "", raw)
        if not token:
            continue

        choice = parse_symbol_keyword(token)
        if choice is None:
            choice = SymbolChoice(symbol=token, display_name=token)

        if choice.symbol in seen_symbols:
            continue

        seen_symbols.add(choice.symbol)
        choices.append(choice)

    return choices


def parse_datecheck_request(message: str) -> tuple[date, list[SymbolChoice]] | None:
    compact = normalize_message(message)
    if not compact.startswith("DATECHECK "):
        return None

    parts = compact.split(" ")
    if len(parts) < 3:
        return None

    raw_date = parts[1]
    try:
        target_date = date.fromisoformat(raw_date)
    except ValueError:
        return None

    choices: list[SymbolChoice] = []
    seen_symbols: set[str] = set()
    for raw in parts[2:]:
        token = re.sub(r"[^A-Z0-9\-\^]", "", raw)
        if not token:
            continue
        choice = parse_symbol_keyword(token)
        if choice is None:
            choice = SymbolChoice(symbol=token, display_name=token)
        if choice.symbol in seen_symbols:
            continue
        seen_symbols.add(choice.symbol)
        choices.append(choice)

    if not choices:
        return None

    return target_date, choices


def parse_ticker_lookup_query(message: str) -> str | None:
    compact = normalize_message(message)
    for keyword in ("TICKER", "LOOKUP", "FIND"):
        if compact == keyword:
            return ""
        if compact.startswith(keyword + " "):
            return compact[len(keyword) + 1 :].strip()
    return None


def search_ticker_profiles(query: str, limit: int = 6) -> list[TickerProfile]:
    term = normalize_message(query)
    if not term:
        return list(TICKER_PROFILES[:limit])

    matched: list[TickerProfile] = []
    for profile in TICKER_PROFILES:
        haystack = " ".join((profile.symbol, profile.display_name, profile.description, *profile.keywords)).upper()
        if term in haystack:
            matched.append(profile)
            if len(matched) >= limit:
                break

    return matched
