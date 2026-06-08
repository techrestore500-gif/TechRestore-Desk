# Market Updates SMS Keyword Menu (2026-06-07)

## Summary

Implemented an interactive inbound SMS keyword assistant for market checks and notification setup under `backend/market_updates`.

The implementation is isolated from Twilio voicemail behavior.

## Webhook route

- `POST /api/market-updates/sms`
- This route is public (no normal app login required), similar to existing Twilio voice webhook handling.

## Storage approach

- Dedicated SQLite file for market assistant state and notifications.
- Default path: `backend/data/market_updates.sqlite`
- Optional override: `MARKET_UPDATES_DB_PATH`

Tables:

- `market_sms_sessions`
- `market_notifications`

## Keyword flows

Main menu:

- `CHECK`
- `REMIND`
- `LIST`
- `STOP`

CHECK flow supports common symbols, `MORE`, and `CUSTOM` ticker input.

REMIND flow supports:

- `PRICE` alerts (`ABOVE` / `BELOW` + threshold + save confirm)
- `TIME` one-time reminders
- `DAILY` recurring reminders

LIST flow supports:

- `DELETE <n>`
- `PAUSE <n>`
- `RESUME <n>`

## Runner commands

From backend directory:

```powershell
python -m market_updates.notification_runner --dry-run
python -m market_updates.notification_runner
```

## Safety notes

- No SMS is sent on module import.
- No recurring scheduler service was added.
- Existing Twilio voicemail routes/services were not modified for behavior.
