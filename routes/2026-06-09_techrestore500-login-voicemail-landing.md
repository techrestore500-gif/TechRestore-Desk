# 2026-06-09 Techrestore500 Login Voicemail Landing

## Summary
- Added a dedicated login redirect behavior so the user `techrestore500@gmail` is sent to `/voicemail` immediately after successful sign-in.
- Created/updated a local active account for `techrestore500@gmail` with password `500tag!!` and `front_desk` role so voicemail access is allowed.

## Frontend Changes
- Updated auth provider login contract to return the authenticated user object after successful login.
- Updated auth gate login submit handler to route `techrestore500@gmail` to `/voicemail` using `window.location.replace`.

## Backend Changes
- Added a narrow legacy email allowlist exception so `techrestore500@gmail` passes email validation.
- Verified authentication succeeds for the requested credentials.

## Verification
- Account creation/update script executed successfully against the backend database.
- Backend login verification succeeded for `techrestore500@gmail` with role `front_desk`.
- Type/lint diagnostics for changed frontend/backend files reported no errors.
