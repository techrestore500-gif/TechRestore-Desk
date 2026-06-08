# Market Updates Admin UI + Feedback Forwarding

Date: 2026-06-08

## Summary

This phase adds owner/admin desk UI controls for market SMS operations and enables optional forwarding of SMS feedback entries to the separate feedback portal ingest endpoint.

## Added UI

New protected page (owner/admin):
- `/market-updates-admin`

Features:
- View active/disabled allowlist entries
- Add allowlist entries
- Disable allowlist entries
- Review invite requests by status (pending/approved/denied)
- Approve or deny pending invite requests
- Review recent feedback submissions

Frontend files:
- `frontend/src/pages/MarketUpdatesAdminPage.tsx`
- `frontend/src/api/marketUpdatesAdmin.ts`
- Route and nav updates in router/app shell

## Feedback forwarding

Backend feedback storage now supports optional forwarding to feedback portal ingest endpoint.

Config (backend service):
- `FEEDBACK_PORTAL_INGEST_URL`
- `FEEDBACK_PORTAL_INGEST_TOKEN` (optional but recommended)

Behavior:
- `FEEDBACK <message>` stores locally in `market_feedback_entries`
- If `FEEDBACK_PORTAL_INGEST_URL` is set, entry is also forwarded by HTTP POST to `/ingest`
- Forward failures are logged and do not break SMS acknowledgement

## Allowlist seed behavior

Allowlist now seeds from any of:
- `MARKET_UPDATES_ALLOWED_NUMBERS`
- `MARKET_UPDATE_TO_NUMBERS`
- `MARKET_UPDATE_TO_NUMBER`

This prevents accidental lockout when only recipient env vars are configured.

## Validation

- Backend focused regressions passed (56 tests)
- Frontend production build passed (`tsc --noEmit` + Vite build)
