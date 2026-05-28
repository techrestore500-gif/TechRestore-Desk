# 2026-05-28 Frontend Auth Gate Production Fix

## Summary
Fixed production desk frontend behavior so unauthenticated users see a shared-password login gate before any protected repair desk UI/data is rendered.

## Changes
- Added app-level auth provider/gate flow for frontend auth-enabled mode:
  - Reads `VITE_AUTH_ENABLED` and enforces login gate when enabled.
  - Shows a simple password-first sign-in screen on first visit.
  - Authenticates via backend shared-password login endpoint (`POST /api/auth/login`) using a fixed desk username and entered password.
- Added centralized API client auth behavior:
  - Automatically injects `Authorization: Bearer <token>` for requests when a session token exists.
  - Invokes global unauthorized handling on any `401` response.
- Added clean expired-token/logout handling:
  - `401` clears local auth session and query cache, then returns user to login gate.
  - Added explicit logout button in app shell when auth is enabled.
- Preserved current backend shared-password architecture without adding roles/user management complexity.

## Validation
- `npm run build` passed.
- Production-style build with explicit env values passed:
  - `VITE_API_BASE_URL=https://api.techrestoredesk.com`
  - `VITE_AUTH_ENABLED=true`
- Built asset marker checks confirmed:
  - API base domain marker present in bundle.
  - Auth session storage key marker present in bundle.
- Auth-focused frontend tests passed:
  - `npx vitest run src/auth/AuthGate.test.tsx src/api/client.auth.test.ts`

## Operational note
- Frontend is now aligned with backend auth gate behavior: no more first-load dashboard view ending in `Request failed: 401`; users are prompted to sign in first.
