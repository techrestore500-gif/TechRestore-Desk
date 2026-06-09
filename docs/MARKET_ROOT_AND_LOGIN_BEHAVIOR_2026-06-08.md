# Market Root and Login Behavior

Date: 2026-06-08

## Changes

- On `market.techrestoredesk.com`, root path `/` now loads Market SMS Admin directly.
- The URL can remain plain `https://market.techrestoredesk.com` (no `/market-updates-admin` suffix required).
- Auth gate branding/copy on market host now shows `Tech Restore Market` and market-focused sign-in text instead of desk wording.

## Files

- `frontend/src/routes/router.tsx`
- `frontend/src/auth/AuthGate.tsx`

## Validation

- Frontend build passed (`npm run build`).
