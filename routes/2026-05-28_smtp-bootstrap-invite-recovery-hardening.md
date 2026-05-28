# 2026-05-28 SMTP Bootstrap Invite Recovery Hardening

## Summary

Implemented production-focused SMTP hardening and bootstrap invite recovery to unblock Render startup onboarding without requiring database resets.

## Backend Changes

- Added SMTP transport mode controls in `backend/app/services/emailer.py`:
  - `SMTP_USE_SSL` to support SSL-on-connect providers (example: Gmail 465)
  - `SMTP_STARTTLS` to control STARTTLS upgrade mode (example: Gmail 587)
  - `SMTP_TIMEOUT_SECONDS` for configurable connection timeout
- Added safe SMTP diagnostics that include exception type and connection mode context (`host`, `port`, `ssl`, `starttls`, `timeout`) without logging credentials or invite tokens.
- Added bootstrap invite resend service flow in `backend/app/services/auth.py`:
  - `resend_bootstrap_admin_invite_from_env()`
  - Revokes any pending bootstrap invite for configured admin email and issues a new one
  - Blocks resend once account setup is complete (users/admin already exist)
- Added protected public endpoint in `backend/app/routes/auth.py`:
  - `POST /api/auth/bootstrap/resend`
  - Requires header `X-Bootstrap-Key` matching `ADMIN_INVITE_BOOTSTRAP_KEY`
- Updated auth gate public allowlist in `backend/app/middleware/auth_gate.py` for bootstrap resend path.
- Updated `backend/.env.example` with:
  - `ADMIN_INVITE_BOOTSTRAP_KEY`
  - `SMTP_USE_SSL`
  - `SMTP_STARTTLS`
  - `SMTP_TIMEOUT_SECONDS`

## Tests Added/Updated

- Added `backend/app/tests/test_emailer.py` covering:
  - STARTTLS path selection
  - SSL path selection
  - SMTP port parse validation
  - Safe diagnostics logging (no secret leakage)
- Extended `backend/app/tests/test_auth_api.py` covering:
  - bootstrap resend key requirement
  - bootstrap resend reissue/revoke flow without DB reset
  - bootstrap resend blocked after admin setup exists

## Validation

- Ran backend test suite subset:
  - `pytest app/tests/test_emailer.py app/tests/test_auth_api.py`
- Result: 25 passed

## Render SMTP Config Profiles

### STARTTLS profile (recommended first)

- `SMTP_HOST=smtp.gmail.com`
- `SMTP_PORT=587`
- `SMTP_USE_SSL=false`
- `SMTP_STARTTLS=true`
- `SMTP_TIMEOUT_SECONDS=20`
- `SMTP_USERNAME=techrestore500@gmail.com`
- `SMTP_PASSWORD=<gmail-app-password>`
- `SMTP_FROM_EMAIL=techrestore500@gmail.com`
- `SMTP_FROM_NAME=Tech Restore`

### SSL fallback profile

- `SMTP_HOST=smtp.gmail.com`
- `SMTP_PORT=465`
- `SMTP_USE_SSL=true`
- `SMTP_STARTTLS=false`
- `SMTP_TIMEOUT_SECONDS=20`
- `SMTP_USERNAME=techrestore500@gmail.com`
- `SMTP_PASSWORD=<gmail-app-password>`
- `SMTP_FROM_EMAIL=techrestore500@gmail.com`
- `SMTP_FROM_NAME=Tech Restore`
