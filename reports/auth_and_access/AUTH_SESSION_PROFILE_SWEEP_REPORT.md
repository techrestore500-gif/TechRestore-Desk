# AUTH_SESSION_PROFILE_SWEEP_REPORT

## Root Cause Summary

The auth/session issues were caused by a combination of frontend session bootstrap gaps and missing account-level endpoints:

1. The frontend trusted cached local auth state immediately on page load without validating the bearer token against `/api/auth/me` before rendering protected views. This allowed stale/expired sessions to briefly render dashboard content and then fail with 401s.
2. 401 errors were surfaced as raw request failures in parts of the UI (`Request failed: 401`), creating confusing user-facing errors instead of a clean sign-in/session-expired state.
3. Invite flow navigation (`Back to sign in`) did not intentionally handle already-authenticated sessions, which could feel like an auto-jump back into the app.
4. A protected change-password endpoint and profile workflow were missing, so account/session management was incomplete.

## Files Inspected

### Frontend
- `frontend/src/api/client.ts`
- `frontend/src/api/auth.ts`
- `frontend/src/auth/AuthProvider.tsx`
- `frontend/src/auth/AuthGate.tsx`
- `frontend/src/auth/config.ts`
- `frontend/src/auth/session.ts`
- `frontend/src/pages/InviteAcceptPage.tsx`
- `frontend/src/routes/router.tsx`
- `frontend/src/components/AppShell.tsx`
- `frontend/src/hooks/useAsyncData.ts`
- `frontend/src/pages/SettingsPage.tsx`
- `frontend/src/pages/AccessRequestsPage.tsx`

### Backend
- `backend/app/routes/auth.py`
- `backend/app/services/auth.py`
- `backend/app/repositories/auth.py`
- `backend/app/auth/dependencies.py`
- `backend/app/middleware/auth_gate.py`
- `backend/app/core/settings.py`
- `backend/app/main.py`
- `backend/app/schemas/auth.py`
- `backend/app/tests/test_auth_api.py`
- `backend/app/tests/test_twilio_api.py`

## Files Changed

### Backend
- `backend/app/schemas/auth.py`
- `backend/app/repositories/auth.py`
- `backend/app/services/auth.py`
- `backend/app/routes/auth.py`
- `backend/app/tests/test_auth_api.py`

### Frontend
- `frontend/src/api/auth.ts`
- `frontend/src/auth/AuthProvider.tsx`
- `frontend/src/auth/AuthGate.tsx`
- `frontend/src/auth/AuthGate.test.tsx`
- `frontend/src/components/AppShell.tsx`
- `frontend/src/hooks/useAsyncData.ts`
- `frontend/src/pages/InviteAcceptPage.tsx`
- `frontend/src/pages/InviteAcceptPage.test.tsx`
- `frontend/src/routes/router.tsx`
- `frontend/src/pages/AccountPage.tsx` (new)
- `frontend/src/pages/LoginStatePage.tsx` (new)

## Backend Fixes

1. Added protected change-password contract:
- New schema: `AuthChangePasswordRequest`
- New schema: `AuthMessageResponse`

2. Added repository password update method:
- `AuthRepository.update_user_password_hash(user_id, password_hash)`

3. Added service-level password change flow:
- `AuthService.change_password(...)`
- Verifies current password using existing hash verification
- Enforces password rules:
  - current required
  - new required
  - min length 8
  - new must differ from current
  - confirm must match
- Re-hashes with existing password hash function
- Writes updated hash only
- Emits audit event without sensitive values

4. Added endpoint:
- `POST /api/auth/change-password`
- Requires bearer token via existing auth dependency
- Returns plain success JSON message
- Rejects shared-password ghost sessions (`id=0`) for password change

5. Preserved protection model:
- No weakening of JWT validation
- Protected routes remain protected
- Twilio public webhooks remain unauthenticated (`/api/twilio/voice`, `/api/twilio/recording`)

## Frontend Fixes

1. Session bootstrap hardening in `AuthProvider`:
- Added startup bootstrap check when token exists
- Calls `fetchCurrentUser(access_token)` before trusting cached session
- If token invalid/expired, clears session + query cache and shows clear sign-in message
- Prevents protected shell from rendering until bootstrap completes

2. Unified unauthorized behavior:
- On protected-request 401 with auth header/token, session is cleared and message is set:
  - `Your session expired. Please sign in again.`

3. Login UX cleanup:
- Login form now surfaces auth session message cleanly
- Message is dismissed when user edits credentials or retries login

4. Invite/login navigation behavior:
- Added explicit `/login` route (`LoginStatePage`) for intentional behavior when already authenticated
- Updated invite page `Back to sign in` to `/login`
- Invite page now handles authenticated sessions explicitly:
  - Shows signed-in state
  - Offers dashboard and sign-out actions
  - Avoids confusing invite acceptance UI while already signed in

5. Friendly 401 error text in data hooks:
- `useAsyncData` maps auth-related raw 401/token errors to a clear session-expired message

## Account/Profile/Change-Password Additions

1. Added `AccountPage` and routed `/account`
2. Added account/profile section in app shell sidebar showing:
- user name
- email
- role
- direct account access and logout
3. Added change-password UI flow in account page:
- current password
- new password
- confirm password
- clear success/error messages
4. Security behavior after successful password change:
- Frontend forces sign-out and re-login

## Tests Added/Updated

### Backend
Updated `backend/app/tests/test_auth_api.py` with:
- login token used to call `GET /api/auth/me`
- change password success path
- old password fails after change
- new password login succeeds
- wrong current password fails
- mismatched confirmation fails

Existing auth/twilio coverage retained for:
- invite acceptance and login flows
- wrong password behavior
- protected routes requiring bearer token
- public Twilio webhooks unauthenticated

### Frontend
Updated:
- `frontend/src/auth/AuthGate.test.tsx`
  - bootstrap loading state before protected app
  - 401 with token clears session and shows session-expired message
- `frontend/src/pages/InviteAcceptPage.test.tsx`
  - wrapped with auth/query providers and auth-enabled config

Existing:
- `frontend/src/api/client.auth.test.ts` still validates Authorization bearer attachment and unauthorized handler behavior

## Commands Run

### Backend
- `pytest app/tests/test_auth_api.py app/tests/test_twilio_api.py`

Result: **43 passed**

### Frontend
- `npm run test -- --run`
- `npm run build`

Result: **24 test files passed (49 tests)** and **build succeeded**

## Manual Production Verification Checklist

1. Clear browser storage once after deploy.
2. Open desk app and sign in.
3. Confirm no raw `Request failed: 401` banners appear for auth/session failures.
4. Confirm protected data loads:
- Tickets (`/api/tickets`)
- Status workflow (`/api/status-workflow`)
- Users/Invites page
- Settings page (including Twilio settings)
5. Confirm account/profile sidebar card shows name, email, role.
6. Open account page and change password:
- wrong current password shows clear error
- valid update succeeds
- user is required to sign in again
- old password fails
- new password succeeds
7. Confirm logout clears session and returns to sign-in UI.
8. Confirm invite link behavior while already signed in is explicit and non-confusing.
9. Confirm Twilio public webhook endpoints continue to accept unauthenticated POSTs.

## Deploy Order

1. Deploy backend first (new `/api/auth/change-password` contract and auth behavior updates).
2. Deploy frontend second (session bootstrap/login/invite/account UX updates).
3. Clear browser storage once after deploy.
4. Login normally and verify protected requests.
5. Verify Users/Invites and Settings/Twilio pages.
6. Verify Logout and Change Password end-to-end.
