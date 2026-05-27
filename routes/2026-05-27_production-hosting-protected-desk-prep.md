# 2026-05-27 Production Hosting + Protected Desk Prep

## Summary
Prepared Tech Restore Desk for first production hosting with a protected desk UI and public Twilio webhook compatibility.

## Backend changes
- Split Twilio routing boundary:
  - Public webhook router: `POST /api/twilio/voice`, `POST /api/twilio/recording`
  - Private Twilio routes remain in authenticated router (`/api/settings/twilio`, `/api/voicemails`, etc)
- Added environment fallback support for Twilio runtime config:
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `TWILIO_PHONE_NUMBER`
  - `PUBLIC_WEBHOOK_BASE_URL`
- Added production CORS helper support for `FRONTEND_ORIGIN`.
- Added `DATABASE_URL` support for SQLite database location override.
- Added `backend/run_server.py` for host/port-aware startup (`PORT`, production bind to `0.0.0.0`).
- Updated Docker backend command to use `${PORT:-8787}`.

## Frontend changes
- Added centralized API URL builder in `src/api/client.ts`.
- API calls now respect `VITE_API_BASE_URL` in production.
- Local behavior stays compatible with `/api` dev proxy.

## Config/docs updates
- Updated env examples with production variables.
- Added deployment runbook: `docs/PRODUCTION_DEPLOYMENT.md`.
- Updated docs index and implementation status.

## Production boundary notes
- Desk UI is intended to be protected externally (Cloudflare Access or equivalent).
- Twilio webhook routes must stay publicly reachable.
- Production should set `TECH_RESTORE_AUTH_BYPASS=0`.
