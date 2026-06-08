from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SymbolChoice:
    symbol: str
    display_name: str


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
    "REMIND",
    "LIST",
    "NOTIFICATIONS",
    "ALERTS",
    "STOP",
    "CANCEL",
}

REMINDER_TYPE_KEYWORDS = {"PRICE", "TIME", "DAILY"}
DIRECTION_KEYWORDS = {"ABOVE", "BELOW"}
CONFIRM_KEYWORDS = {"SAVE", "YES", "CONFIRM", "EDIT", "DELETE", "STOP", "CANCEL"}


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
