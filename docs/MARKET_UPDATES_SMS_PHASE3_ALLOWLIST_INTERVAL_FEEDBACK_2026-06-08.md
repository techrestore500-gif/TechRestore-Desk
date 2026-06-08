# Market Updates SMS Phase 3: Allowlist, Interval Reminders, Feedback

Date: 2026-06-08

## Delivered

This phase adds inbound phone access control, invite drafting, interval reminder scheduling, and feedback persistence, while preserving existing Twilio behavior.

### Inbound allowlist and invite drafts

- Added allowlist storage and admin CRUD support.
- Inbound SMS now blocks numbers not on allowlist.
- Blocked numbers can submit invite requests via SMS:
  - `REQUEST <name>`
  - `INVITE <name>`
  - `ACCESS <name>`
- Added invite request approval/denial and allowlist management API routes under:
  - `/api/market-updates/admin/*`

### Interval reminders

- Added reminder type keyword `UPDATE` / `INTERVAL`.
- New flow supports:
  - custom or symbol-based message
  - interval minutes (minimum 30)
  - start datetime
  - stop datetime
- Added runner support for interval cadence and stop-window completion.

### Feedback

- `FEEDBACK <text>` now persists feedback entries.
- Added admin feedback listing endpoint:
  - `GET /api/market-updates/admin/feedback`
- Added separate feedback portal service scaffold in `feedback_service/` for deployment at `feedback.techrestoredesk.com`.

## Files touched

- `backend/market_updates/storage.py`
- `backend/market_updates/allowlist.py`
- `backend/market_updates/keyword_handlers.py`
- `backend/market_updates/notifications.py`
- `backend/market_updates/notification_runner.py`
- `backend/market_updates/feedback_store.py`
- `backend/app/routes/market_updates_admin.py`
- `backend/app/main.py`
- `feedback_service/main.py`
- `feedback_service/run.py`
- `feedback_service/requirements.txt`
- `render.yaml`

## Validation

Focused suite passed:
- 56 passed, 0 failed.

Includes:
- market updates
- keyword flow
- notification runner
- Twilio regression tests
