# 2026-06-07 Market Updates SMS Standalone Feature

## Change intent

Add a small, isolated market update SMS sender using Twilio without modifying the existing voicemail flow.

## Delivery scope

- New package: `backend/market_updates`
- Modules:
  - `config.py`
  - `market_data.py`
  - `formatter.py`
  - `sms_sender.py`
  - `send_market_update.py`
  - `README.md`
- Tests: `backend/app/tests/test_market_updates.py`
- Dependencies updated in `backend/requirements.txt`

Additional completion pass:

- Multi-recipient support via `MARKET_UPDATE_TO_NUMBERS` with fallback to `MARKET_UPDATE_TO_NUMBER`
- Per-recipient send results with continue-on-error behavior
- CLI one-time scheduling via `--send-at HH:MM` and optional `--tomorrow`
- Dry-run output now includes intended recipients

## Isolation confirmation

No changes were made to voicemail API routes or voicemail service behavior.

## Operations

From `backend`:

- Dry run:
  - `python -m market_updates.send_market_update --dry-run`
- Real send:
  - `python -m market_updates.send_market_update`
- Override destination number:
  - `python -m market_updates.send_market_update --to +18483291230,+19296529336`
- One-time local-time schedule (2:00 PM):
  - `python -m market_updates.send_market_update --send-at 14:00`
