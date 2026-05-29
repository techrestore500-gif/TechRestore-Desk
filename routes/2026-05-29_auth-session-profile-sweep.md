# 2026-05-29 Auth Session Profile Sweep

## Scope

Full auth/session/profile cleanup for login, session bootstrap, unauthorized handling, invite/login navigation behavior, logout reliability, and account change-password flow.

## Route/API Notes

### Added
- `POST /api/auth/change-password`

Request body:
```json
{
  "current_password": "...",
  "new_password": "...",
  "confirm_password": "..."
}
```

Response:
```json
{
  "message": "Password changed successfully. Please sign in again."
}
```

### Existing Confirmed
- `POST /api/auth/login`
- `GET /api/auth/me`
- Invite routes under `/api/auth/invites/*`
- Public unauthenticated Twilio webhook routes:
  - `POST /api/twilio/voice`
  - `POST /api/twilio/recording`

## Frontend Route Notes

### Added
- `/login` (intentional already-signed-in state)
- `/account` (profile + change password + logout)

### Updated
- Invite page back-to-sign-in now points to `/login`
- Invite page shows explicit state when user is already authenticated

## Deploy Reminder

- Deploy backend first
- Deploy frontend second
- Clear browser storage once
- Verify login, protected requests, users/invites, settings/twilio, logout, and change-password
