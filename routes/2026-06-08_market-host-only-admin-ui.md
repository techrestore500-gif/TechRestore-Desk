# 2026-06-08 Market Host Only Admin UI

Updated frontend routing/navigation so Market SMS Admin is only exposed on `market.techrestoredesk.com`.

- Hidden from desk navigation and settings shortcut on non-market hosts.
- Non-market direct route hits redirect to market host route.

Validation:
- `npm run build` passed in `frontend/`.
