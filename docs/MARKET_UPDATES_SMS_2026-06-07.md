# Market Updates SMS Feature (2026-06-07)

## Summary

A new standalone Python package was added at `backend/market_updates` to send short market update SMS messages using Twilio.

This package is intentionally isolated from existing backend routes and Twilio voicemail functionality.

## Included capabilities

- Environment-based configuration validation for required Twilio and destination values.
- Supports either `MARKET_UPDATE_TO_NUMBERS` (comma-separated) or fallback `MARKET_UPDATE_TO_NUMBER`.
- Reuses the repo's existing Twilio env pattern for auth credentials: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_PHONE_NUMBER`/`TWILIO_FROM_NUMBER`.
- Market quote retrieval through `yfinance` for configurable symbols.
- Graceful partial-failure behavior when one or more symbols are unavailable.
- Concise SMS formatter with price and percent change output.
- CLI entry point with dry run support, multi-recipient destination override, and one-time local-time scheduling via `--send-at`.

## Commands

From `backend`:

- Dry run: `python -m market_updates.send_market_update --dry-run`
- Real send: `python -m market_updates.send_market_update`
- Override destination(s): `python -m market_updates.send_market_update --to +18483291230,+19296529336`
- Schedule once at 2:40 PM local: `python -m market_updates.send_market_update --send-at 14:40`

## Required environment variables

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_NUMBER` or existing repo-compatible `TWILIO_PHONE_NUMBER`
- One of:
	- `MARKET_UPDATE_TO_NUMBERS` (preferred)
	- `MARKET_UPDATE_TO_NUMBER` (fallback)

## Optional environment variables

- `MARKET_UPDATE_SYMBOLS` (default: `^GSPC,BTC-USD`)
- `MARKET_UPDATE_PROVIDER` (default: `yfinance`)
- `--tomorrow` CLI flag if using `--send-at` and you want next-day scheduling when today's time has passed

## Current intended recipients

Current internal recipients are documented as:

- `+18483291230`
- `+19296529336`

Set them through environment variables, not in code:

```dotenv
MARKET_UPDATE_TO_NUMBERS=+18483291230,+19296529336
MARKET_UPDATE_SYMBOLS=^GSPC,^IXIC,BTC-USD
MARKET_UPDATE_PROVIDER=yfinance
```

## Local send timing note

The one-shot schedule command uses local machine time. For a 2:40 PM Eastern send, run the CLI on a machine configured to Eastern time / America/New_York and use `--send-at 14:40`.

## Command examples

```powershell
cd "c:\Users\owner\Desktop\Tech Restore\tech-restore-desk\backend"
& "c:\Users\owner\Desktop\Tech Restore\.venv\Scripts\python.exe" -m market_updates.send_market_update --send-at 14:40 --to +18483291230,+19296529336
```

```powershell
cd "c:\Users\owner\Desktop\Tech Restore\tech-restore-desk\backend"
& "c:\Users\owner\Desktop\Tech Restore\.venv\Scripts\python.exe" -m market_updates.send_market_update --dry-run --to +18483291230,+19296529336
```

```powershell
cd "c:\Users\owner\Desktop\Tech Restore\tech-restore-desk\backend"
& "c:\Users\owner\Desktop\Tech Restore\.venv\Scripts\python.exe" -m market_updates.send_market_update --to +18483291230,+19296529336
```

```powershell
cd "c:\Users\owner\Desktop\Tech Restore\tech-restore-desk\backend"
& "c:\Users\owner\Desktop\Tech Restore\.venv\Scripts\python.exe" -m market_updates.send_market_update --dry-run --to +18483291230,+19296529336
```

## Dependencies added

- `yfinance==0.2.52`
- `twilio==9.2.3`
