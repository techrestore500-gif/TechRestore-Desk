from __future__ import annotations

import re
from datetime import datetime, timedelta

from market_updates.keywords import (
    CONFIRM_KEYWORDS,
    DIRECTION_KEYWORDS,
    REMINDER_TYPE_KEYWORDS,
    SYMBOL_ALIASES,
    TOP_LEVEL_KEYWORDS,
    normalize_message,
    parse_list_action,
    parse_symbol_keyword,
)
from market_updates.market_data import fetch_market_data
from market_updates.notifications import (
    build_summary,
    create_notification,
    delete_notification_for_recipient,
    get_notification_by_index,
    list_notifications_for_recipient,
    set_notification_enabled_for_recipient,
)
from market_updates.session_state import STATE_IDLE, clear_session, get_session, save_session

STATE_CHECK_CHOOSE_SYMBOL = "check_choose_symbol"
STATE_CHECK_CUSTOM_SYMBOL = "check_custom_symbol"
STATE_REMIND_CHOOSE_TYPE = "remind_choose_type"
STATE_PRICE_CHOOSE_SYMBOL = "price_choose_symbol"
STATE_PRICE_CUSTOM_SYMBOL = "price_custom_symbol"
STATE_PRICE_CHOOSE_DIRECTION = "price_choose_direction"
STATE_PRICE_CHOOSE_THRESHOLD = "price_choose_threshold"
STATE_TIME_CHOOSE_MESSAGE = "time_choose_message"
STATE_TIME_CUSTOM_MESSAGE = "time_custom_message"
STATE_TIME_CHOOSE_TIME = "time_choose_time"
STATE_DAILY_CHOOSE_MESSAGE = "daily_choose_message"
STATE_DAILY_CUSTOM_MESSAGE = "daily_custom_message"
STATE_DAILY_CHOOSE_TIME = "daily_choose_time"
STATE_PENDING_CONFIRM = "pending_confirm"


def _main_menu() -> str:
    return (
        "Market Assistant:\n"
        "CHECK - check prices\n"
        "REMIND - set notifications\n"
        "LIST - view notifications\n"
        "STOP - cancel current setup"
    )


def _check_menu() -> str:
    return (
        "What do you want to check?\n"
        "BTC - Bitcoin\n"
        "ETH - Ethereum\n"
        "SPX - S&P 500\n"
        "NASDAQ - Nasdaq\n"
        "DOW - Dow Jones\n"
        "SPY - SPY ETF\n"
        "QQQ - QQQ ETF\n"
        "AAPL - Apple\n"
        "MORE - more choices"
    )


def _check_more_menu() -> str:
    return (
        "More choices:\n"
        "TSLA - Tesla\n"
        "NVDA - Nvidia\n"
        "CUSTOM - enter a ticker\n"
        "CHECK - back to main list"
    )


def _remind_type_menu() -> str:
    return (
        "What kind of notification do you want?\n"
        "PRICE - above/below price alert\n"
        "TIME - one-time reminder\n"
        "DAILY - daily update\n"
        "LIST - current notifications"
    )


def _price_symbol_menu() -> str:
    return (
        "Which market do you want to watch?\n"
        "BTC - Bitcoin\n"
        "ETH - Ethereum\n"
        "SPX - S&P 500\n"
        "NASDAQ - Nasdaq\n"
        "SPY - SPY ETF\n"
        "AAPL - Apple\n"
        "MORE - more choices"
    )


def _price_more_menu() -> str:
    return (
        "More choices:\n"
        "DOW - Dow Jones\n"
        "QQQ - QQQ ETF\n"
        "TSLA - Tesla\n"
        "NVDA - Nvidia\n"
        "CUSTOM - enter a ticker"
    )


def _time_message_menu() -> str:
    return (
        "What update should I send?\n"
        "STATUS - market snapshot\n"
        "BTC - Bitcoin\n"
        "SPX - S&P 500\n"
        "NASDAQ - Nasdaq\n"
        "CUSTOM - custom message"
    )


def _parse_threshold(text: str) -> float | None:
    cleaned = text.replace("$", "").replace(",", "").strip()
    if not re.fullmatch(r"\d+(\.\d+)?", cleaned):
        return None
    value = float(cleaned)
    if value <= 0:
        return None
    return value


def _parse_time_of_day(text: str) -> tuple[str, str] | None:
    value = text.strip().upper()
    for fmt in ("%H:%M", "%I:%M %p", "%I %p"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%H:%M"), dt.strftime("%I:%M %p").lstrip("0")
        except ValueError:
            continue
    return None


def _build_time_iso_next_occurrence(hhmm_24: str) -> str:
    now = datetime.now()
    hour, minute = [int(part) for part in hhmm_24.split(":", 1)]
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target = target + timedelta(days=1)
    return target.isoformat()


def _render_quote_sentence(symbol: str, display_name: str) -> str:
    quote = fetch_market_data([symbol], provider="yfinance")[0]
    if not quote.available or quote.latest_price is None or quote.daily_percent_change is None:
        return f"{display_name} is currently unavailable. Reply CHECK for options."

    price = quote.latest_price
    pct = quote.daily_percent_change
    direction = "up" if pct >= 0 else "down"
    abs_pct = abs(pct)
    if symbol.startswith("^"):
        price_text = f"{price:,.2f}"
    else:
        price_text = f"${price:,.2f}"

    return (
        f"{display_name} is at {price_text}, {direction} {abs_pct:.2f}% today.\n"
        "Reply CHECK to check another, or REMIND to set a notification."
    )


def _format_notifications_list(from_number: str) -> str:
    notifications = list_notifications_for_recipient(from_number)
    if not notifications:
        return "You have no notifications yet. Reply REMIND to create one."

    lines = ["Your notifications:"]
    for index, notification in enumerate(notifications, start=1):
        status = "active" if int(notification.get("enabled", 0)) == 1 else "paused"
        lines.append(f"{index}. {build_summary(notification)} - {status}")

    lines.append("Reply DELETE 1, PAUSE 1, or RESUME 1.")
    return "\n".join(lines)


def _handle_list_action(from_number: str, action: str, index: int) -> str:
    notification = get_notification_by_index(from_number, index)
    if notification is None:
        return "That notification number was not found. Reply LIST to view your notifications."

    notification_id = int(notification["id"])

    if action == "DELETE":
        deleted = delete_notification_for_recipient(from_number, notification_id)
        if deleted:
            return "Deleted. Reply LIST to view notifications, or REMIND to create another."
        return "Could not delete that notification. Reply LIST and try again."

    if action == "PAUSE":
        changed = set_notification_enabled_for_recipient(from_number, notification_id, enabled=False)
        if changed:
            return "Paused. Reply LIST to view notifications, or RESUME 1 to reactivate."
        return "Could not pause that notification. Reply LIST and try again."

    if action == "RESUME":
        changed = set_notification_enabled_for_recipient(from_number, notification_id, enabled=True)
        if changed:
            return "Resumed. Reply LIST to view notifications, or CHECK to check prices."
        return "Could not resume that notification. Reply LIST and try again."

    return "Unknown action. Reply LIST to view notifications."


def _save_draft_notification(from_number: str, draft: dict) -> str:
    notification_type = str(draft.get("notification_type") or "")

    if notification_type == "price_alert":
        threshold_value = float(draft.get("threshold"))
        notification = create_notification(
            recipient_phone=from_number,
            notification_type="price_alert",
            symbol=draft.get("symbol"),
            display_name=draft.get("display_name"),
            condition=draft.get("direction"),
            threshold=threshold_value,
            reminder_time=None,
            recurrence=None,
            original_text=f"{draft.get('display_name')} {draft.get('direction')} ${threshold_value:,.2f}",
        )
        clear_session(from_number)
        return (
            f"Saved. I will text you when {notification.get('display_name')} "
            f"{notification.get('condition')} ${float(notification.get('threshold')):,.2f}.\n"
            "Reply LIST to view notifications, or CHECK to check prices."
        )

    if notification_type == "one_time_reminder":
        notification = create_notification(
            recipient_phone=from_number,
            notification_type="one_time_reminder",
            symbol=draft.get("symbol"),
            display_name=draft.get("display_name"),
            condition=None,
            threshold=None,
            reminder_time=draft.get("reminder_time"),
            recurrence="once",
            original_text=str(draft.get("message") or "One-time reminder"),
        )
        clear_session(from_number)
        return (
            f"Saved. One-time reminder set for {notification.get('reminder_time')} local time.\n"
            "Reply LIST to view notifications, or CHECK to check prices."
        )

    if notification_type == "daily_reminder":
        notification = create_notification(
            recipient_phone=from_number,
            notification_type="daily_reminder",
            symbol=draft.get("symbol"),
            display_name=draft.get("display_name"),
            condition=None,
            threshold=None,
            reminder_time=draft.get("reminder_time"),
            recurrence="daily",
            original_text=str(draft.get("message") or "Daily reminder"),
        )
        clear_session(from_number)
        return (
            f"Saved. Daily reminder set for {notification.get('reminder_time')} local time.\n"
            "Reply LIST to view notifications, or CHECK to check prices."
        )

    clear_session(from_number)
    return "Could not save that draft. Reply REMIND to start again."


def handle_inbound_market_sms(from_number: str, body: str) -> str:
    message = normalize_message(body)
    if not from_number.strip():
        return _main_menu()

    session = get_session(from_number)
    state = session.state
    draft = dict(session.draft)

    if message in {"HELP", "MENU"}:
        save_session(from_number, state=STATE_IDLE, draft={})
        return _main_menu()

    if message in {"STOP", "CANCEL"}:
        clear_session(from_number)
        return "Canceled. Reply MENU for options, CHECK for prices, or REMIND for notifications."

    if message in {"LIST", "NOTIFICATIONS", "ALERTS"}:
        save_session(from_number, state=STATE_IDLE, draft={})
        return _format_notifications_list(from_number)

    list_action = parse_list_action(message)
    if list_action is not None:
        action, index = list_action
        save_session(from_number, state=STATE_IDLE, draft={})
        return _handle_list_action(from_number, action, index)

    if state == STATE_IDLE:
        if message == "CHECK":
            save_session(from_number, state=STATE_CHECK_CHOOSE_SYMBOL, draft={})
            return _check_menu()
        if message == "REMIND":
            save_session(from_number, state=STATE_REMIND_CHOOSE_TYPE, draft={})
            return _remind_type_menu()
        return _main_menu()

    if state == STATE_CHECK_CHOOSE_SYMBOL:
        if message == "MORE":
            return _check_more_menu()
        if message == "CUSTOM":
            save_session(from_number, state=STATE_CHECK_CUSTOM_SYMBOL, draft={})
            return "Reply with a ticker symbol, like MSFT or AMZN."

        choice = parse_symbol_keyword(message)
        if choice is None:
            return "Unknown symbol. Reply BTC, ETH, SPX, NASDAQ, DOW, SPY, QQQ, AAPL, MORE, or CUSTOM."

        clear_session(from_number)
        return _render_quote_sentence(choice.symbol, choice.display_name)

    if state == STATE_CHECK_CUSTOM_SYMBOL:
        ticker = re.sub(r"[^A-Z0-9\-\^]", "", message)
        if not ticker:
            return "Please reply with a valid ticker symbol, like MSFT."

        clear_session(from_number)
        return _render_quote_sentence(ticker, ticker)

    if state == STATE_REMIND_CHOOSE_TYPE:
        if message not in REMINDER_TYPE_KEYWORDS:
            return "Reply PRICE, TIME, DAILY, or LIST."

        if message == "PRICE":
            save_session(
                from_number,
                state=STATE_PRICE_CHOOSE_SYMBOL,
                draft={"notification_type": "price_alert"},
            )
            return _price_symbol_menu()

        if message == "TIME":
            save_session(
                from_number,
                state=STATE_TIME_CHOOSE_MESSAGE,
                draft={"notification_type": "one_time_reminder"},
            )
            return _time_message_menu()

        save_session(
            from_number,
            state=STATE_DAILY_CHOOSE_MESSAGE,
            draft={"notification_type": "daily_reminder"},
        )
        return _time_message_menu()

    if state == STATE_PRICE_CHOOSE_SYMBOL:
        if message == "MORE":
            return _price_more_menu()

        if message == "CUSTOM":
            save_session(from_number, state=STATE_PRICE_CUSTOM_SYMBOL, draft=draft)
            return "Reply with a ticker symbol, like MSFT or AMZN."

        choice = parse_symbol_keyword(message)
        if choice is None:
            return "Reply with a symbol like BTC, ETH, SPX, NASDAQ, SPY, AAPL, MORE, or CUSTOM."

        draft["symbol"] = choice.symbol
        draft["display_name"] = choice.display_name
        save_session(from_number, state=STATE_PRICE_CHOOSE_DIRECTION, draft=draft)
        return f"{choice.display_name} selected. Reply BELOW for a drop alert, or ABOVE for a rise alert."

    if state == STATE_PRICE_CUSTOM_SYMBOL:
        ticker = re.sub(r"[^A-Z0-9\-\^]", "", message)
        if not ticker:
            return "Please reply with a valid ticker symbol, like MSFT."

        draft["symbol"] = ticker
        draft["display_name"] = ticker
        save_session(from_number, state=STATE_PRICE_CHOOSE_DIRECTION, draft=draft)
        return f"{ticker} selected. Reply BELOW for a drop alert, or ABOVE for a rise alert."

    if state == STATE_PRICE_CHOOSE_DIRECTION:
        if message not in DIRECTION_KEYWORDS:
            return "Reply BELOW for a drop alert, or ABOVE for a rise alert."

        draft["direction"] = message.lower()
        save_session(from_number, state=STATE_PRICE_CHOOSE_THRESHOLD, draft=draft)
        return "What price should trigger the alert? Example: 60000"

    if state == STATE_PRICE_CHOOSE_THRESHOLD:
        threshold = _parse_threshold(message)
        if threshold is None:
            return "Please reply with a numeric price like 60000."

        draft["threshold"] = threshold
        summary = f"{draft.get('display_name')} {draft.get('direction')} ${threshold:,.2f}."
        draft["summary"] = summary
        save_session(from_number, state=STATE_PENDING_CONFIRM, draft=draft)
        return (
            f"Alert draft:\n{summary}\n"
            "Reply SAVE to activate, EDIT to change, or DELETE to cancel."
        )

    if state == STATE_TIME_CHOOSE_MESSAGE:
        if message == "CUSTOM":
            save_session(from_number, state=STATE_TIME_CUSTOM_MESSAGE, draft=draft)
            return "Reply with the one-time reminder message."

        if message == "STATUS":
            draft["message"] = "Market status update"
            draft["symbol"] = None
            draft["display_name"] = "Market status"
        else:
            choice = parse_symbol_keyword(message)
            if choice is None:
                return "Reply STATUS, BTC, SPX, NASDAQ, or CUSTOM."
            draft["message"] = f"{choice.display_name} update"
            draft["symbol"] = choice.symbol
            draft["display_name"] = choice.display_name

        save_session(from_number, state=STATE_TIME_CHOOSE_TIME, draft=draft)
        return "What time should I send it? Example: 9:30 AM"

    if state == STATE_TIME_CUSTOM_MESSAGE:
        if not message:
            return "Please reply with reminder text."
        draft["message"] = body.strip()
        draft["symbol"] = None
        draft["display_name"] = "Custom"
        save_session(from_number, state=STATE_TIME_CHOOSE_TIME, draft=draft)
        return "What time should I send it? Example: 9:30 AM"

    if state == STATE_TIME_CHOOSE_TIME:
        parsed = _parse_time_of_day(message)
        if parsed is None:
            return "Reply with a time like 14:30 or 2:30 PM."

        hhmm_24, human_time = parsed
        draft["reminder_time"] = _build_time_iso_next_occurrence(hhmm_24)
        draft["human_time"] = human_time
        save_session(from_number, state=STATE_PENDING_CONFIRM, draft=draft)
        return (
            f"Reminder draft:\nOne-time update at {human_time}.\n"
            "Reply SAVE to activate, EDIT to change, or DELETE to cancel."
        )

    if state == STATE_DAILY_CHOOSE_MESSAGE:
        if message == "CUSTOM":
            save_session(from_number, state=STATE_DAILY_CUSTOM_MESSAGE, draft=draft)
            return "Reply with the daily update text."

        if message == "STATUS":
            draft["message"] = "Daily market status update"
            draft["symbol"] = None
            draft["display_name"] = "Market status"
        else:
            choice = parse_symbol_keyword(message)
            if choice is None:
                return "Reply STATUS, BTC, SPX, NASDAQ, or CUSTOM."
            draft["message"] = f"{choice.display_name} daily update"
            draft["symbol"] = choice.symbol
            draft["display_name"] = choice.display_name

        save_session(from_number, state=STATE_DAILY_CHOOSE_TIME, draft=draft)
        return "What daily time should I use? Example: 9:30 AM"

    if state == STATE_DAILY_CUSTOM_MESSAGE:
        if not message:
            return "Please reply with daily reminder text."
        draft["message"] = body.strip()
        draft["symbol"] = None
        draft["display_name"] = "Custom"
        save_session(from_number, state=STATE_DAILY_CHOOSE_TIME, draft=draft)
        return "What daily time should I use? Example: 9:30 AM"

    if state == STATE_DAILY_CHOOSE_TIME:
        parsed = _parse_time_of_day(message)
        if parsed is None:
            return "Reply with a time like 14:30 or 2:30 PM."

        hhmm_24, human_time = parsed
        draft["reminder_time"] = hhmm_24
        draft["human_time"] = human_time
        save_session(from_number, state=STATE_PENDING_CONFIRM, draft=draft)
        return (
            f"Reminder draft:\nDaily update at {human_time}.\n"
            "Reply SAVE to activate, EDIT to change, or DELETE to cancel."
        )

    if state == STATE_PENDING_CONFIRM:
        if message not in CONFIRM_KEYWORDS:
            return "Reply SAVE to activate, EDIT to change, or DELETE to cancel."

        if message in {"SAVE", "YES", "CONFIRM"}:
            return _save_draft_notification(from_number, draft)

        if message == "DELETE":
            clear_session(from_number)
            return "Draft deleted. Reply REMIND to start again, or CHECK to check prices."

        if message == "EDIT":
            notification_type = str(draft.get("notification_type") or "")
            if notification_type == "price_alert":
                save_session(from_number, state=STATE_PRICE_CHOOSE_THRESHOLD, draft=draft)
                return "Reply with a new trigger price. Example: 60000"
            if notification_type == "one_time_reminder":
                save_session(from_number, state=STATE_TIME_CHOOSE_TIME, draft=draft)
                return "Reply with a new time. Example: 9:30 AM"
            if notification_type == "daily_reminder":
                save_session(from_number, state=STATE_DAILY_CHOOSE_TIME, draft=draft)
                return "Reply with a new daily time. Example: 9:30 AM"
            clear_session(from_number)
            return "Could not edit that draft. Reply REMIND to start again."

    save_session(from_number, state=STATE_IDLE, draft={})
    return _main_menu()
