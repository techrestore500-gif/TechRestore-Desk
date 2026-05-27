# 2026-05-27 Backend Go-Live Blockers: Shared Password Auth + Render Hardening

## Summary
Implemented backend blocker fixes required before first production go-live on Render.

## Changes
- Added shared-password auth flow using environment variables:
  - `REPAIR_DESK_AUTH_ENABLED`
  - `REPAIR_DESK_PASSWORD`
- Added global API auth gate middleware:
  - Protects private API routes when auth is enabled
  - Keeps these public routes unauthenticated:
    - `POST /api/twilio/voice`
    - `POST /api/twilio/recording`
    - `POST /api/auth/login`
    - `GET /api/health`
- Updated auth token handling to support shared-password session tokens without pre-seeded DB users.
- Improved production startup warning messages to include explicit missing variable names (including `DATABASE_URL`).
- Added regression tests for shared-password login and route protection split.
- Ensured tests are isolated from ambient shell production env leakage.

## Validation
- Targeted backend suites passing:
  - `test_auth_api.py`
  - `test_twilio_api.py`
  - `test_observability_and_settings.py`
- Verified private route requires token when auth enabled.
- Verified Twilio webhook public routes still accessible without token.
- Verified startup warns loudly when production runs without `DATABASE_URL`.

## Operational note
- Render persistent disk is still required for production SQLite durability.
