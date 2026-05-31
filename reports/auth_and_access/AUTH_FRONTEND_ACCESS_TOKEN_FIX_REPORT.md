# Auth Frontend Access Token Fix Report

## Root Cause

The immediate sign-out after successful login was caused by frontend auth state timing and 401 handling behavior, not a backend schema mismatch.

The frontend already read `access_token` correctly from the login response in `AuthProvider.tsx`. However, there was a race condition:

1. Login succeeded and React state was updated with the new token.
2. Before the `useEffect` that refreshes the API token provider ran, protected requests could fire.
3. Those requests were sent without `Authorization` because the provider still returned the previous token (`null`).
4. Backend returned `401`.
5. Global unauthorized handler always cleared session on any `401`, including requests that had no bearer token.
6. User was signed out immediately.

This exactly matches the observed behavior: brief dashboard entry followed by 401 and forced logout.

## Files Changed

- `frontend/src/auth/AuthProvider.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/auth/session.ts`
- `frontend/src/api/client.auth.test.ts`

## Exact Fix

### 1) Ensure login stores and uses `access_token` immediately

In `AuthProvider.tsx`:

- Kept backend response contract: `access_token`, `token_type`, `expires_at`, `user`.
- Added strict check that `access_token` exists after login; throws safe error if missing.
- Set token provider immediately in `loginWithCredentials` with the new token before state updates to avoid the post-login race window.
- Continued persisting `{ accessToken, user }` to storage per existing design.

### 2) Only auto-logout on authenticated 401s

In `client.ts`:

- Tracked whether an `Authorization` header was actually present on each request.
- Unauthorized handler now runs only when:
  - response status is 401, and
  - unauthorized handler is registered, and
  - request actually carried Authorization.

This prevents tokenless 401s from wiping a valid newly-created session.

### 3) Session load compatibility

In `session.ts`:

- `loadSession()` now supports legacy stored keys (`access_token` or `token`) in addition to current `accessToken`.
- This improves reload/session continuity across older stored payload variants.

### 4) Test coverage added

In `client.auth.test.ts`:

- Updated existing 401 unauthorized test to include a token provider.
- Added test: no unauthorized callback when 401 happens without token.
- Added test: unauthorized callback fires when explicit Authorization header is present.

## Tests / Build Commands Run

From `frontend/`:

```powershell
npm run test -- --run src/api/client.auth.test.ts src/auth/AuthGate.test.tsx
npm run build
```

Results:

- Frontend auth tests: passed (9/9)
- Frontend build: passed (`tsc --noEmit` + Vite production build)

## Deploy Order

1. Deploy frontend (this fix is frontend-only).
2. Verify login flow on production:
   - Login with invited account.
   - Confirm dashboard remains loaded.
   - Confirm protected API calls include `Authorization: Bearer <access_token>`.
3. Hard refresh and verify session persists as intended.
4. Verify 401 behavior still logs out only when a tokened request is rejected.

## Security Notes

- No auth weakening was introduced.
- No public signup was added.
- No tokens, passwords, or hashes are logged.
- Existing invite-only auth behavior remains intact.
