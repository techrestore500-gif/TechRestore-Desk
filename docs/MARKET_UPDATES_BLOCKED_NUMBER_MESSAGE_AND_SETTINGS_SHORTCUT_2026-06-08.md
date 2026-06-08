# Market Updates Blocked Number Message + Settings Shortcut

Date: 2026-06-08

## Summary

Updated the blocked-number SMS response for market updates to a polite support-first message and added a Settings shortcut to Market SMS Admin.

## Changes

### Blocked-number response text

When an inbound number is not allowed, the assistant now replies with:
- a polite explanation that this number is not enabled for market text support
- guidance to call Tech Restore to leave a message instead of texting
- immediate support contact: `8483291230` (call/text)
- optional access path: `REQUEST <name>`

Implementation:
- `backend/market_updates/keyword_handlers.py`

### Settings shortcut

Added direct navigation from Settings to Market SMS Admin:
- `Market SMS admin` button in the Settings sections controls row

Implementation:
- `frontend/src/pages/SettingsPage.tsx`

## Validation

- Backend focused tests passed (45 passed)
- Frontend production build passed
