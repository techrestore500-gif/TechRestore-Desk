from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime, timedelta
from typing import Sequence

from market_updates.config import load_config, parse_phone_numbers
from market_updates.formatter import format_market_update_sms
from market_updates.market_data import fetch_market_data
from market_updates.sms_sender import send_market_update_sms_to_many

logger = logging.getLogger(__name__)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a Tech Restore market update SMS")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and format update, then print it without sending SMS")
    parser.add_argument("--to", dest="to_override", help="Override destination phone number(s), comma-separated")
    parser.add_argument("--send-at", dest="send_at", help="Wait and send once at local time HH:MM (24-hour)")
    parser.add_argument("--tomorrow", action="store_true", help="Allow scheduling for tomorrow if --send-at time has passed today")
    return parser.parse_args(argv)


def _now_local() -> datetime:
    return datetime.now()


def _parse_hhmm(value: str) -> tuple[int, int]:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError("--send-at must use HH:MM 24-hour format, e.g. 14:00")

    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError as exc:
        raise ValueError("--send-at must use HH:MM 24-hour format, e.g. 14:00") from exc

    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError("--send-at must use HH:MM in valid 24-hour time range")
    return hour, minute


def _resolve_target_recipients(config_to_numbers: list[str], to_override: str | None) -> list[str]:
    if to_override is None:
        return list(config_to_numbers)
    return parse_phone_numbers(to_override, env_var_name="--to")


def _wait_until_local_time_once(send_at: str, recipient_count: int, *, allow_tomorrow: bool = False) -> None:
    hour, minute = _parse_hhmm(send_at)
    now = _now_local()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if target <= now:
        if not allow_tomorrow:
            raise ValueError(
                "Requested --send-at time has already passed today. Re-run with a future time or add --tomorrow."
            )
        target = target + timedelta(days=1)

    delay_seconds = (target - now).total_seconds()
    human_time = target.strftime("%I:%M %p").lstrip("0")
    print(
        f"Market update scheduled to send once at {human_time} local time to {recipient_count} recipients."
    )
    time.sleep(delay_seconds)


def run(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        config = load_config()
    except ValueError as exc:
        logger.error("Configuration error: %s", exc)
        return 1

    quotes = fetch_market_data(config.symbols, provider=config.provider)
    message_body = format_market_update_sms(quotes)

    recipients = _resolve_target_recipients(config.to_numbers, args.to_override)

    if args.send_at:
        try:
            _wait_until_local_time_once(args.send_at, len(recipients), allow_tomorrow=args.tomorrow)
        except ValueError as exc:
            logger.error("Scheduling error: %s", exc)
            return 1

    if args.dry_run:
        print(message_body)
        print(f"Would send to: {', '.join(recipients)}")
        print("Dry run complete. SMS not sent.")
        return 0

    results = send_market_update_sms_to_many(
        twilio_account_sid=config.twilio_account_sid,
        twilio_auth_token=config.twilio_auth_token,
        from_number=config.twilio_from_number,
        to_numbers=recipients,
        message_body=message_body,
    )

    had_failure = False
    for result in results:
        if result.success:
            print(f"{result.to_number}: sent (SID: {result.message_sid})")
            continue
        had_failure = True
        print(f"{result.to_number}: failed ({result.error_message or 'unknown error'})")

    if had_failure:
        logger.error("One or more recipients failed to receive market update SMS")
        return 1

    print("Market update SMS send completed successfully for all recipients.")
    return 0


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    raise SystemExit(run())


if __name__ == "__main__":
    main()
