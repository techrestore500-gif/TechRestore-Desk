# 2026-06-07 Market Updates SMS Keyword Menu

## Objective

Add an inbound SMS keyword menu and notification runner for market updates, while keeping existing Twilio voicemail behavior intact.

## Delivered

- `backend/market_updates/session_state.py`
- `backend/market_updates/keywords.py`
- `backend/market_updates/notifications.py`
- `backend/market_updates/keyword_handlers.py`
- `backend/market_updates/notification_runner.py`
- `backend/market_updates/storage.py`

## API integration

- New public route: `POST /api/market-updates/sms`
- Added to auth middleware public path allowlist.

## Test coverage additions

- `backend/app/tests/test_market_update_keywords.py`
- `backend/app/tests/test_market_update_notifications.py`

## Notes

- Session and notification persistence use a dedicated SQLite database for isolation.
- Runner is manual one-shot CLI only; no recurring scheduler introduced.
