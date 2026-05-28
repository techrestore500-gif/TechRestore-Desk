# 2026-05-28 Account Login + Access Request Approval Flow

## Summary
Replaced temporary shared-password frontend login gate with account-based authentication and controlled signup approval.

## Backend changes
- Expanded user auth model to include:
  - `name`, `email`, `username`
  - `role` (`owner`, `admin`, `technician`, `front_desk`, `viewer`)
  - `status` (`pending`, `active`, `denied`, `disabled`)
  - `approved_at`, `approved_by`
- Added migration-safe auth table updates in repository layer for existing databases.
- Added identifier-based login support (`username` or `email`) on `POST /api/auth/login`.
- Added public signup request endpoint:
  - `POST /api/auth/signup`
  - creates `pending` access request only (no token returned)
- Added admin/owner access-request management endpoints:
  - `GET /api/auth/access-requests`
  - `POST /api/auth/access-requests/{id}/approve` (with role assignment)
  - `POST /api/auth/access-requests/{id}/deny`
- Added startup bootstrap owner flow from env vars when no users exist:
  - `ADMIN_EMAIL`, `ADMIN_NAME`, `ADMIN_PASSWORD`
- Preserved Twilio public webhook unauthenticated routes:
  - `POST /api/twilio/voice`
  - `POST /api/twilio/recording`
- Kept `REPAIR_DESK_PASSWORD` shared-password mode as optional fallback.

## Frontend changes
- Replaced password-only auth gate with full login/request-access UI:
  - Login fields: username/email + password
  - Request access fields: name, email, password, confirm password
- Login stores bearer token and session as before.
- Global API client continues to auto-attach bearer token.
- Any API `401` clears auth session and returns user to login screen.
- Added sidebar/admin page for pending approvals:
  - `Access Requests`
  - approve with role selection or deny

## Validation
- Backend tests:
  - `python -m pytest app/tests/test_auth_api.py app/tests/test_twilio_api.py app/tests/test_audit_api.py`
  - Result: `31 passed`
- Backend import check:
  - `python -c "from app.main import app; print('import ok')"`
  - Result: `import ok`
- Frontend tests:
  - `npx vitest run src/auth/AuthGate.test.tsx src/api/client.auth.test.ts src/pages/AccessRequestsPage.test.tsx`
  - Result: `9 passed`
- Frontend build:
  - `npm run build`
  - Result: pass
- Production-style frontend build:
  - `VITE_API_BASE_URL=https://api.techrestoredesk.com`
  - `VITE_AUTH_ENABLED=true`
  - `npm run build`
  - Result: pass
