# 2026-05-29 Bootstrap Invite Autosend Redeploy Spam Fix

## Problem

Production redeploys could send another bootstrap invite email when startup detected no users/admins.

## Root Cause

Startup always called bootstrap invite creation with email sending enabled.

When production SQLite was reset or empty at startup, the app treated it like first boot and sent another invite.

## Fix

- Added startup-level autosend flag: `ADMIN_INVITE_BOOTSTRAP_AUTOSEND`
- Default startup behavior is now no email autosend (`false`)
- Bootstrap invite records can still be created when enabled, but startup only emails when autosend is explicitly turned on
- Manual recovery path remains: `POST /api/auth/bootstrap/resend` with `X-Bootstrap-Key`

## Files Changed

- `backend/app/core/startup.py`
- `backend/app/services/auth.py`
- `backend/app/tests/test_auth_api.py`
- `backend/.env.example`
- `docs/ENVIRONMENT_CONFIGURATION.md`

## Validation

- Ran `python -m pytest app/tests/test_auth_api.py -k bootstrap`
- Result: `5 passed`
