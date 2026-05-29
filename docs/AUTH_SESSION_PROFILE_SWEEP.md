# Auth Session Profile Sweep (2026-05-29)

This document tracks the complete auth/session/profile stabilization pass across backend and frontend.

## What Changed

- Added backend endpoint: `POST /api/auth/change-password` (protected)
- Added backend validation for current/new/confirm password workflow
- Added secure password hash update path using existing hash implementation
- Added frontend auth bootstrap validation via `/api/auth/me` before trusting stored session
- Added frontend session-expired handling for protected-request 401s
- Added explicit `/login` behavior for already-authenticated sessions
- Added account/profile page with:
  - user name
  - email
  - role
  - logout
  - change password form
- Added sidebar account/profile visibility and direct account navigation
- Normalized user-facing 401 messaging to avoid raw `Request failed: 401`

## Security Rules Preserved

- Invite-only access is unchanged
- No public signup added
- Protected backend routes remain protected
- Twilio public webhook routes remain unauthenticated:
  - `POST /api/twilio/voice`
  - `POST /api/twilio/recording`
- No JWT/token/password/hash exposure added to logs/UI

## Verification Summary

- Backend tests: auth + twilio suites passed
- Frontend tests: full test suite passed
- Frontend build: passed

See root report for full implementation and rollout details:
- `AUTH_SESSION_PROFILE_SWEEP_REPORT.md`
