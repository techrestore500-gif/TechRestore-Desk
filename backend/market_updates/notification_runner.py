from __future__ import annotations

import argparse
import logging
from datetime import datetime
from typing import Sequence

from market_updates.config import load_config
from market_updates.market_data import fetch_market_data
from market_updates.notifications import (
    list_due_notifications,
    mark_notification_triggered,
    update_last_triggered,
)
from market_updates.sms_sender import send_market_update_sms

logger = logging.getLogger(__name__)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run market update notification checks")
    parser.add_argument("--dry-run", action="store_true", help="Print due notifications without sending")
    return parser.parse_args(argv)


def _now_local() -> datetime:
    return datetime.now()


def _daily_due(notification: dict, now: datetime) -> bool:
    reminder_time = str(notification.get("reminder_time") or "")
    if not reminder_time:
        return False

    try:
        hour, minute = [int(part) for part in reminder_time.split(":", 1)]
    except ValueError:
        return False

    if (now.hour, now.minute) < (hour, minute):
        return False

    last_triggered_raw = notification.get("last_triggered_at")
    if not last_triggered_raw:
        return True

    try:
        last_triggered = datetime.fromisoformat(str(last_triggered_raw))
    except ValueError:
        return True

    return last_triggered.date() != now.date()


def _one_time_due(notification: dict, now: datetime) -> bool:
    reminder_time = notification.get("reminder_time")
    if not reminder_time:
        return False

    try:
        due_at = datetime.fromisoformat(str(reminder_time))
    except ValueError:
        return False

    return due_at <= now


def _price_due(notification: dict) -> bool:
    symbol = notification.get("symbol")
    condition = str(notification.get("condition") or "").lower()
    threshold = notification.get("threshold")

    if not symbol or threshold is None or condition not in {"above", "below"}:
        return False

    quote = fetch_market_data([str(symbol)], provider="yfinance")[0]
    if not quote.available or quote.latest_price is None:
        return False

    latest = quote.latest_price
    trigger_value = float(threshold)

    if condition == "above":
        return latest >= trigger_value
    return latest <= trigger_value


def _interval_due(notification: dict, now: datetime) -> bool:
    start_raw = notification.get("reminder_time")
    stop_raw = notification.get("stop_time")
    interval_minutes = int(notification.get("interval_minutes") or 0)

    if not start_raw or not stop_raw or interval_minutes < 30:
        return False

    try:
        start_at = datetime.fromisoformat(str(start_raw))
        stop_at = datetime.fromisoformat(str(stop_raw))
    except ValueError:
        return False

    if now < start_at or now > stop_at:
        return False

    last_triggered_raw = notification.get("last_triggered_at")
    if not last_triggered_raw:
        return True

    try:
        last_triggered = datetime.fromisoformat(str(last_triggered_raw))
    except ValueError:
        return True

    elapsed_seconds = (now - last_triggered).total_seconds()
    return elapsed_seconds >= interval_minutes * 60


def _build_notification_message(notification: dict) -> str:
    notification_type = str(notification.get("type") or "")
    display_name = str(notification.get("display_name") or notification.get("symbol") or "Market")

    if notification_type == "price_alert":
        direction = str(notification.get("condition") or "").lower()
        threshold = float(notification.get("threshold") or 0)
        direction_text = "rose above" if direction == "above" else "fell below"
        return f"Alert: {display_name} {direction_text} ${threshold:,.2f}."

    if notification_type == "one_time_reminder":
        original = str(notification.get("original_text") or "One-time market reminder")
        return f"Reminder: {original}"

    if notification_type == "daily_reminder":
        original = str(notification.get("original_text") or "Daily market reminder")
        return f"Daily update: {original}"

    if notification_type == "interval_reminder":
        original = str(notification.get("original_text") or "Interval market reminder")
        return f"Update: {original}"

    return "Market notification"


def run(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        config = load_config()
    except ValueError as exc:
        logger.error("Configuration error: %s", exc)
        return 1

    now = _now_local()
    notifications = list_due_notifications()

    due_items: list[dict] = []
    for item in notifications:
        notification_type = str(item.get("type") or "")
        if notification_type == "interval_reminder":
            stop_raw = item.get("stop_time")
            if stop_raw:
                try:
                    stop_at = datetime.fromisoformat(str(stop_raw))
                    if now > stop_at:
                        mark_notification_triggered(int(item["id"]), complete=True, triggered_at=now.isoformat())
                        continue
                except ValueError:
                    pass

        if notification_type == "price_alert" and _price_due(item):
            due_items.append(item)
        elif notification_type == "one_time_reminder" and _one_time_due(item, now):
            due_items.append(item)
        elif notification_type == "daily_reminder" and _daily_due(item, now):
            due_items.append(item)
        elif notification_type == "interval_reminder" and _interval_due(item, now):
            due_items.append(item)

    if not due_items:
        print("No notifications due.")
        return 0

    print(f"Due notifications: {len(due_items)}")

    for item in due_items:
        notification_id = int(item["id"])
        to_number = str(item["recipient_phone"])
        message_body = _build_notification_message(item)

        if args.dry_run:
            print(f"[DRY-RUN] Would send to {to_number}: {message_body}")
            continue

        result = send_market_update_sms(
            twilio_account_sid=config.twilio_account_sid,
            twilio_auth_token=config.twilio_auth_token,
            from_number=config.twilio_from_number,
            to_number=to_number,
            message_body=message_body,
        )

        if not result.success:
            print(f"{to_number}: failed ({result.error_message or 'unknown error'})")
            continue

        print(f"{to_number}: sent (SID: {result.message_sid})")

        notification_type = str(item.get("type") or "")
        if notification_type in {"price_alert", "one_time_reminder"}:
            mark_notification_triggered(notification_id, complete=True, triggered_at=now.isoformat())
        elif notification_type == "daily_reminder":
            update_last_triggered(notification_id, triggered_at=now.isoformat())
        elif notification_type == "interval_reminder":
            if item.get("stop_time"):
                try:
                    stop_at = datetime.fromisoformat(str(item.get("stop_time")))
                    if now >= stop_at:
                        mark_notification_triggered(notification_id, complete=True, triggered_at=now.isoformat())
                    else:
                        update_last_triggered(notification_id, triggered_at=now.isoformat())
                except ValueError:
                    update_last_triggered(notification_id, triggered_at=now.isoformat())
            else:
                update_last_triggered(notification_id, triggered_at=now.isoformat())

    return 0


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    raise SystemExit(run())


if __name__ == "__main__":
    main()
