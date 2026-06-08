from __future__ import annotations

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from market_updates.allowlist import create_or_update_invite_request, is_number_allowed
from market_updates.keywords import (
    CONFIRM_KEYWORDS,
    DIRECTION_KEYWORDS,
    REMINDER_TYPE_KEYWORDS,
    SYMBOL_ALIASES,
    TOP_LEVEL_KEYWORDS,
    normalize_message,
    parse_check_symbols,
    parse_datecheck_request,
    parse_list_action,
    parse_symbol_keyword,
    parse_ticker_lookup_query,
    search_ticker_profiles,
)
from market_updates.market_data import fetch_market_data, fetch_market_data_for_date
from market_updates.feedback_store import create_feedback_entry
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
STATE_INTERVAL_CHOOSE_MESSAGE = "interval_choose_message"
STATE_INTERVAL_CUSTOM_MESSAGE = "interval_custom_message"
STATE_INTERVAL_CHOOSE_MINUTES = "interval_choose_minutes"
STATE_INTERVAL_CHOOSE_START = "interval_choose_start"
STATE_INTERVAL_CHOOSE_STOP = "interval_choose_stop"
STATE_PENDING_CONFIRM = "pending_confirm"


def _main_menu() -> str:
    return (
        "Market Assistant:\n"
        "CHECK - check prices\n"
        "DATECHECK - historical close (YYYY-MM-DD symbols)\n"
        "TICKER/LOOKUP/FIND - symbol finder\n"
        "FEEDBACK - send product feedback\n"
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
        "UPDATE - repeat every N minutes\n"
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


def _parse_local_datetime(text: str) -> tuple[str, str] | None:
    value = text.strip()
    formats = (
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %I:%M %p",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %I:%M %p",
    )
    for fmt in formats:
        try:
            dt = datetime.strptime(value.upper(), fmt)
            dt = dt.replace(tzinfo=ZoneInfo("America/New_York"))
            return dt.isoformat(), dt.strftime("%b %d %Y %I:%M %p ET")
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


def _parse_interval_minutes(text: str) -> int | None:
    compact = re.sub(r"[^0-9]", "", text)
    if not compact:
        return None
    minutes = int(compact)
    if minutes < 30:
        return None
    if minutes > 1440:
        return None
    return minutes


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


def _render_quote_list_sentence(raw_choices: list[tuple[str, str]]) -> str:
    symbols = [item[0] for item in raw_choices]
    quotes = fetch_market_data(symbols, provider="yfinance")

    lines = ["Latest prices:"]
    for choice, quote in zip(raw_choices, quotes):
        _symbol, display_name = choice
        if not quote.available or quote.latest_price is None or quote.daily_percent_change is None:
            lines.append(f"{display_name}: unavailable")
            continue

        direction = "up" if quote.daily_percent_change >= 0 else "down"
        abs_pct = abs(quote.daily_percent_change)
        price_text = f"{quote.latest_price:,.2f}" if quote.symbol.startswith("^") else f"${quote.latest_price:,.2f}"
        lines.append(f"{display_name}: {price_text}, {direction} {abs_pct:.2f}%")

    lines.append("Reply CHECK for menu, DATECHECK for historical, or REMIND for alerts.")
    return "\n".join(lines)


def _render_datecheck_response(target_iso_date: str, raw_choices: list[tuple[str, str]]) -> str:
    symbols = [item[0] for item in raw_choices]
    quotes = fetch_market_data_for_date(symbols, datetime.fromisoformat(target_iso_date).date(), provider="yfinance")

    lines = [f"Close on {target_iso_date}:"]
    for choice, quote in zip(raw_choices, quotes):
        _symbol, display_name = choice
        if not quote.available or quote.close_price is None:
            lines.append(f"{display_name}: unavailable")
            continue

        price_text = f"{quote.close_price:,.2f}" if quote.symbol.startswith("^") else f"${quote.close_price:,.2f}"
        lines.append(f"{display_name}: {price_text}")

    lines.append("Reply CHECK <tickers> for live, or DATECHECK YYYY-MM-DD <tickers> again.")
    return "\n".join(lines)


def _render_ticker_lookup(message: str) -> str:
    parsed_query = parse_ticker_lookup_query(message)
    if parsed_query is None:
        return "Reply TICKER <company or symbol>. Example: TICKER apple"

    profiles = search_ticker_profiles(parsed_query, limit=6)
    if not profiles:
        return "No matches found. Try a different keyword, like TICKER microsoft or FIND btc."

    lines = ["Ticker matches:"]
    for profile in profiles:
        lines.append(f"{profile.symbol} - {profile.display_name}: {profile.description}")
    lines.append("Use CHECK <ticker list> to fetch live values.")
    return "\n".join(lines)


def _format_human_datetime(value: object) -> str:
    if value is None:
        return "n/a"

    raw = str(value).strip()
    if not raw:
        return "n/a"

    if re.fullmatch(r"\d{2}:\d{2}", raw):
        try:
            parsed = datetime.strptime(raw, "%H:%M")
            return parsed.strftime("%b %d %Y %I:%M %p ET")
        except ValueError:
            return raw

    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("America/New_York"))
        dt = dt.astimezone(ZoneInfo("America/New_York"))
        return dt.strftime("%b %d %Y %I:%M %p ET")
    except ValueError:
        return raw


def _format_notifications_list(from_number: str) -> str:
    notifications = list_notifications_for_recipient(from_number)
    if not notifications:
        return "You have no notifications yet. Reply REMIND to create one."

    lines = ["Your notifications:"]
    for index, notification in enumerate(notifications, start=1):
        status = "active" if int(notification.get("enabled", 0)) == 1 else "paused"
        created_at = _format_human_datetime(notification.get("created_at"))
        schedule_at = _format_human_datetime(notification.get("reminder_time"))
        lines.append(f"{index}. {build_summary(notification)} | {status} | created {created_at} | when {schedule_at}")

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
            stop_time=None,
            recurrence=None,
            interval_minutes=None,
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
            stop_time=None,
            recurrence="once",
            interval_minutes=None,
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
            stop_time=None,
            recurrence="daily",
            interval_minutes=None,
            original_text=str(draft.get("message") or "Daily reminder"),
        )
        clear_session(from_number)
        return (
            f"Saved. Daily reminder set for {notification.get('reminder_time')} local time.\n"
            "Reply LIST to view notifications, or CHECK to check prices."
        )

    if notification_type == "interval_reminder":
        notification = create_notification(
            recipient_phone=from_number,
            notification_type="interval_reminder",
            symbol=draft.get("symbol"),
            display_name=draft.get("display_name"),
            condition=None,
            threshold=None,
            reminder_time=draft.get("start_time"),
            stop_time=draft.get("stop_time"),
            recurrence="interval",
            interval_minutes=int(draft.get("interval_minutes") or 0),
            original_text=str(draft.get("message") or "Interval reminder"),
        )
        clear_session(from_number)
        return (
            "Saved. Interval reminder is active every "
            f"{notification.get('interval_minutes')} minutes from {notification.get('reminder_time')} to {notification.get('stop_time')}.\n"
            "Reply LIST to view notifications, or CHECK to check prices."
        )

    clear_session(from_number)
    return "Could not save that draft. Reply REMIND to start again."


def handle_inbound_market_sms(from_number: str, body: str) -> str:
    message = normalize_message(body)
    if not from_number.strip():
        return _main_menu()

    if not is_number_allowed(from_number):
        if message.startswith("REQUEST") or message.startswith("INVITE") or message.startswith("ACCESS"):
            request_text = body.strip()
            label = ""
            if " " in request_text:
                label = request_text.split(" ", 1)[1].strip()
            create_or_update_invite_request(from_number, message_text=request_text, requested_label=label or None)
            return (
                "Access request sent. Your number is pending approval. "
                "We will notify you after approval."
            )

        create_or_update_invite_request(from_number, message_text=body.strip() or None)
        return (
            "Thanks for contacting Tech Restore. This number is not enabled for market text support. "
            "To leave a message for Tech Restore, please call us instead of texting. "
            "For immediate support, call or text 8483291230. "
            "If you need market text access, reply REQUEST <your name>."
        )

    session = get_session(from_number)
    state = session.state
    draft = dict(session.draft)

    if message in {"HELP", "MENU"}:
        save_session(from_number, state=STATE_IDLE, draft={})
        return _main_menu()

    if message.startswith("CHECK "):
        parsed = parse_check_symbols(message)
        if not parsed:
            return "Reply CHECK <ticker list>, for example: CHECK BTC AAPL TSLA"
        return _render_quote_list_sentence([(item.symbol, item.display_name) for item in parsed])

    if message.startswith("DATECHECK "):
        parsed = parse_datecheck_request(message)
        if parsed is None:
            return "Use DATECHECK YYYY-MM-DD <ticker list>, for example: DATECHECK 2026-06-01 BTC AAPL"
        target_date, choices = parsed
        return _render_datecheck_response(target_date.isoformat(), [(item.symbol, item.display_name) for item in choices])

    ticker_query = parse_ticker_lookup_query(message)
    if ticker_query is not None:
        return _render_ticker_lookup(message)

    if message == "FEEDBACK":
        return "Reply with FEEDBACK <your message>. We log it for review at feedback.techrestoredesk.com."

    if message.startswith("FEEDBACK "):
        feedback_text = body.strip()[9:].strip() if len(body.strip()) >= 9 else ""
        if not feedback_text:
            return "Please include feedback text after FEEDBACK."
        create_feedback_entry(from_number, feedback_text, source="sms")
        return "Thanks, your feedback was received and queued for review."

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
        if message == "DATECHECK":
            return "Use DATECHECK YYYY-MM-DD <ticker list>, for example: DATECHECK 2026-06-01 BTC AAPL"
        if message in {"TICKER", "LOOKUP", "FIND"}:
            return "Reply with TICKER <company or symbol>, for example: TICKER apple"
        if message == "REMIND":
            save_session(from_number, state=STATE_REMIND_CHOOSE_TYPE, draft={})
            return _remind_type_menu()
        return _main_menu()

    if state == STATE_CHECK_CHOOSE_SYMBOL:
        if " " in message:
            parsed = parse_check_symbols(f"CHECK {message}")
            if parsed:
                clear_session(from_number)
                return _render_quote_list_sentence([(item.symbol, item.display_name) for item in parsed])

        if message == "MORE":
            return _check_more_menu()
        if message == "CUSTOM":
            save_session(from_number, state=STATE_CHECK_CUSTOM_SYMBOL, draft={})
            return "Reply with a ticker symbol, like MSFT or AMZN."

        choice = parse_symbol_keyword(message)
        if choice is None:
            return "Unknown symbol. Reply BTC, ETH, SPX, NASDAQ, DOW, SPY, QQQ, AAPL, MORE, CUSTOM, or CHECK <ticker list>."

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
            return "Reply PRICE, TIME, DAILY, UPDATE, or LIST."

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

        if message in {"UPDATE", "INTERVAL"}:
            save_session(
                from_number,
                state=STATE_INTERVAL_CHOOSE_MESSAGE,
                draft={"notification_type": "interval_reminder"},
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
        return "What date and time should I send it? Example: 2026-06-20 9:30 AM"

    if state == STATE_TIME_CUSTOM_MESSAGE:
        if not message:
            return "Please reply with reminder text."
        draft["message"] = body.strip()
        draft["symbol"] = None
        draft["display_name"] = "Custom"
        save_session(from_number, state=STATE_TIME_CHOOSE_TIME, draft=draft)
        return "What date and time should I send it? Example: 2026-06-20 9:30 AM"

    if state == STATE_TIME_CHOOSE_TIME:
        parsed = _parse_local_datetime(body)
        if parsed is None:
            return "Reply with date and time like 2026-06-20 14:30 or 06/20/2026 2:30 PM."

        reminder_time_iso, human_time = parsed
        draft["reminder_time"] = reminder_time_iso
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

    if state == STATE_INTERVAL_CHOOSE_MESSAGE:
        if message == "CUSTOM":
            save_session(from_number, state=STATE_INTERVAL_CUSTOM_MESSAGE, draft=draft)
            return "Reply with the repeated update text."

        if message == "STATUS":
            draft["message"] = "Interval market status update"
            draft["symbol"] = None
            draft["display_name"] = "Market status"
        else:
            choice = parse_symbol_keyword(message)
            if choice is None:
                return "Reply STATUS, BTC, SPX, NASDAQ, or CUSTOM."
            draft["message"] = f"{choice.display_name} interval update"
            draft["symbol"] = choice.symbol
            draft["display_name"] = choice.display_name

        save_session(from_number, state=STATE_INTERVAL_CHOOSE_MINUTES, draft=draft)
        return "How often should I send it? Minimum is 30 minutes. Example: 60"

    if state == STATE_INTERVAL_CUSTOM_MESSAGE:
        if not message:
            return "Please reply with update text."
        draft["message"] = body.strip()
        draft["symbol"] = None
        draft["display_name"] = "Custom"
        save_session(from_number, state=STATE_INTERVAL_CHOOSE_MINUTES, draft=draft)
        return "How often should I send it? Minimum is 30 minutes. Example: 60"

    if state == STATE_INTERVAL_CHOOSE_MINUTES:
        minutes = _parse_interval_minutes(body)
        if minutes is None:
            return "Reply with minutes as a number (minimum 30). Example: 60"

        draft["interval_minutes"] = minutes
        save_session(from_number, state=STATE_INTERVAL_CHOOSE_START, draft=draft)
        return "What start date and time should I use? Example: 2026-06-20 09:00"

    if state == STATE_INTERVAL_CHOOSE_START:
        parsed = _parse_local_datetime(body)
        if parsed is None:
            return "Reply with start date/time like 2026-06-20 09:00 or 06/20/2026 9:00 AM."

        start_iso, start_human = parsed
        draft["start_time"] = start_iso
        draft["start_human_time"] = start_human
        save_session(from_number, state=STATE_INTERVAL_CHOOSE_STOP, draft=draft)
        return "What stop date and time should I use? Example: 2026-06-20 18:00"

    if state == STATE_INTERVAL_CHOOSE_STOP:
        parsed = _parse_local_datetime(body)
        if parsed is None:
            return "Reply with stop date/time like 2026-06-20 18:00 or 06/20/2026 6:00 PM."

        stop_iso, stop_human = parsed
        start_iso = str(draft.get("start_time") or "")
        try:
            start_dt = datetime.fromisoformat(start_iso)
            stop_dt = datetime.fromisoformat(stop_iso)
        except ValueError:
            return "Could not parse start/stop window. Reply REMIND to restart."

        if stop_dt <= start_dt:
            return "Stop time must be after start time. Reply with a later stop date and time."

        draft["stop_time"] = stop_iso
        draft["stop_human_time"] = stop_human
        summary = (
            f"{draft.get('display_name')} every {draft.get('interval_minutes')} minutes, "
            f"from {draft.get('start_human_time')} to {draft.get('stop_human_time')}."
        )
        draft["summary"] = summary
        save_session(from_number, state=STATE_PENDING_CONFIRM, draft=draft)
        return (
            f"Reminder draft:\n{summary}\n"
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
                return "Reply with a new date and time. Example: 2026-06-20 9:30 AM"
            if notification_type == "daily_reminder":
                save_session(from_number, state=STATE_DAILY_CHOOSE_TIME, draft=draft)
                return "Reply with a new daily time. Example: 9:30 AM"
            if notification_type == "interval_reminder":
                save_session(from_number, state=STATE_INTERVAL_CHOOSE_STOP, draft=draft)
                return "Reply with a new stop date and time. Example: 2026-06-20 18:00"
            clear_session(from_number)
            return "Could not edit that draft. Reply REMIND to start again."

    save_session(from_number, state=STATE_IDLE, draft={})
    return _main_menu()
