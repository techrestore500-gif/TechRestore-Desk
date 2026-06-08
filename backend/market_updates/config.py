from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_MARKET_UPDATE_SYMBOLS = ["^GSPC", "BTC-USD"]
DEFAULT_MARKET_UPDATE_PROVIDER = "yfinance"


@dataclass(frozen=True)
class MarketUpdateConfig:
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_from_number: str
    to_numbers: list[str]
    symbols: list[str]
    provider: str


def _first_non_empty_env(name: str, env: dict[str, str]) -> str | None:
    raw_value = env.get(name)
    if raw_value is None:
        return None
    value = raw_value.strip()
    return value or None


def _parse_symbols(value: str | None) -> list[str]:
    if value is None:
        return list(DEFAULT_MARKET_UPDATE_SYMBOLS)

    symbols = [item.strip() for item in value.split(",") if item.strip()]
    if not symbols:
        return list(DEFAULT_MARKET_UPDATE_SYMBOLS)

    unique_symbols: list[str] = []
    seen: set[str] = set()
    for symbol in symbols:
        if symbol in seen:
            continue
        seen.add(symbol)
        unique_symbols.append(symbol)
    return unique_symbols


def parse_phone_numbers(value: str, *, env_var_name: str) -> list[str]:
    numbers = [item.strip() for item in value.split(",") if item.strip()]
    if not numbers:
        raise ValueError(f"{env_var_name} must contain at least one non-blank phone number")

    unique_numbers: list[str] = []
    seen: set[str] = set()
    for number in numbers:
        if number in seen:
            continue
        seen.add(number)
        unique_numbers.append(number)
    return unique_numbers


def _resolve_to_numbers(values: dict[str, str]) -> list[str]:
    to_numbers_raw = _first_non_empty_env("MARKET_UPDATE_TO_NUMBERS", values)
    if to_numbers_raw is not None:
        return parse_phone_numbers(to_numbers_raw, env_var_name="MARKET_UPDATE_TO_NUMBERS")

    to_number_raw = _first_non_empty_env("MARKET_UPDATE_TO_NUMBER", values)
    if to_number_raw is None:
        raise ValueError(
            "Missing required environment variable: MARKET_UPDATE_TO_NUMBERS or MARKET_UPDATE_TO_NUMBER"
        )
    return parse_phone_numbers(to_number_raw, env_var_name="MARKET_UPDATE_TO_NUMBER")


def load_config(env: dict[str, str] | None = None) -> MarketUpdateConfig:
    values = dict(os.environ if env is None else env)

    required_keys = [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
    ]

    missing_keys = [key for key in required_keys if _first_non_empty_env(key, values) is None]
    if _first_non_empty_env("TWILIO_FROM_NUMBER", values) is None and _first_non_empty_env("TWILIO_PHONE_NUMBER", values) is None:
        missing_keys.append("TWILIO_FROM_NUMBER or TWILIO_PHONE_NUMBER")
    if missing_keys:
        joined = ", ".join(missing_keys)
        raise ValueError(f"Missing required environment variables: {joined}")

    provider = (_first_non_empty_env("MARKET_UPDATE_PROVIDER", values) or DEFAULT_MARKET_UPDATE_PROVIDER).lower()
    to_numbers = _resolve_to_numbers(values)
    twilio_from_number = _first_non_empty_env("TWILIO_FROM_NUMBER", values) or _first_non_empty_env("TWILIO_PHONE_NUMBER", values)

    return MarketUpdateConfig(
        twilio_account_sid=_first_non_empty_env("TWILIO_ACCOUNT_SID", values) or "",
        twilio_auth_token=_first_non_empty_env("TWILIO_AUTH_TOKEN", values) or "",
        twilio_from_number=twilio_from_number or "",
        to_numbers=to_numbers,
        symbols=_parse_symbols(_first_non_empty_env("MARKET_UPDATE_SYMBOLS", values)),
        provider=provider,
    )
