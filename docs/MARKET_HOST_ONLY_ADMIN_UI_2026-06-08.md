# Market Host Only Admin UI

Date: 2026-06-08

## Change

Restricted Market SMS Admin frontend access to market host only.

## Behavior

- Market SMS Admin nav item is hidden unless host is `market.techrestoredesk.com` (or local/dev hosts).
- Settings page shortcut to Market SMS Admin is hidden unless host is `market.techrestoredesk.com` (or local/dev hosts).
- Direct navigation to `/market-updates-admin` from non-market hosts redirects to `https://market.techrestoredesk.com/market-updates-admin`.

## Files

- `frontend/src/components/AppShell.tsx`
- `frontend/src/routes/router.tsx`
- `frontend/src/pages/SettingsPage.tsx`

## Validation

- Frontend production build passed.
