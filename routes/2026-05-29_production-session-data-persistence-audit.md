# 2026-05-29 Production Session / Data Persistence Audit

## Summary

Completed a focused production-readiness audit for session stability, SQLite persistence, Twilio voicemail persistence, and voicemail greeting persistence after the auth/session/profile sweep.

## Findings

- No new broad frontend auth/session regression was found in the current login/bootstrap/logout flow.
- JWT expiry remains 60 minutes and can still cause expected sign-outs.
- Users, Twilio settings, voicemail greeting settings, and voicemail inbox records all persist in the same SQLite database.
- If production is using an ephemeral SQLite path such as `sqlite:///./data/tech_restore_desk.sqlite`, Render redeploys can wipe all of that state together.
- That makes persistence/config drift the top-ranked explanation for the reported production incident.

## Code Changes

- Added admin-only backend endpoint: `GET /api/system/runtime-diagnostics`
- Endpoint returns safe runtime DB diagnostics only:
  - database type
  - effective database path
  - whether `DATABASE_URL` is configured
  - whether SQLite is under `/var/data`
  - persistence classification and warning

## Documentation Updates

- Added root report: `PRODUCTION_SESSION_DATA_PERSISTENCE_AUDIT.md`
- Updated `docs/PRODUCTION_DEPLOYMENT.md`
- Updated `docs/ENVIRONMENT_CONFIGURATION.md`

## Validation

- Ran: `python -m pytest app/tests/test_observability_and_settings.py app/tests/test_twilio_api.py`
- Result: `24 passed`
