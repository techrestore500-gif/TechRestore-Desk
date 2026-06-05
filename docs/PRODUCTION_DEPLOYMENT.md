# Production Deployment Runbook (Protected Repair Desk)

This runbook prepares Tech Restore Desk for first live hosting with:
- protected desk UI at `https://desk.<domain>`
- public API at `https://api.<domain>`
- publicly reachable Twilio webhooks

## Target topology

- Frontend: `desk.<domain>`
- Backend API: `api.<domain>`
- Public webhook routes (must stay open to Twilio):
  - `POST /api/twilio/voice`
  - `POST /api/twilio/recording`
- Private app routes: all other `/api/*` routes (expected to be reached by authorized desk users and/or backend auth)

## Security model for v1

- The desk UI is protected externally (Cloudflare Access or equivalent).
- Twilio webhooks are intentionally not behind browser login protection.
- Backend route auth is available, but `TECH_RESTORE_AUTH_BYPASS=1` allows bypass.
- Production must set `TECH_RESTORE_AUTH_BYPASS=0`.

Risk note:
If API routes are reachable without network policy + backend auth enforcement, direct API access is possible even when the UI is protected. For v1, enforce both:
- Cloudflare Access on `desk.<domain>`
- `TECH_RESTORE_AUTH_BYPASS=0` on backend

## Local dev environment

Backend local defaults remain supported. For explicit local setup:
- `APP_ENV=development`
- `REPAIR_DESK_AUTH_ENABLED=false`
- `DATABASE_URL=./data/tech_restore_desk.sqlite`
- `CORS_ALLOWED_ORIGINS=http://127.0.0.1:6173,http://localhost:6173`

Frontend local defaults:
- If `VITE_API_BASE_URL` is unset, app calls `http://127.0.0.1:8787` in development mode.
- `VITE_AUTH_ENABLED=true`

## Production env variables

Backend required variables:
- `PORT` (provided by host in most PaaS platforms)
- `PYTHON_VERSION=3.11.9`
- `REPAIR_DESK_AUTH_ENABLED=true`
- `PUBLIC_BASE_URL=https://api.<domain>`
- `CORS_ALLOWED_ORIGINS=https://desk.<domain>`
- `DATABASE_URL` (SQLite path or sqlite URL, for example `/var/data/tech_restore_desk.sqlite` or `sqlite:////var/data/tech_restore_desk.sqlite`)
- `SECRET_KEY=<secret>`

Backend required for Twilio voicemail:
- `TWILIO_ACCOUNT_SID=<secret>`
- `TWILIO_AUTH_TOKEN=<secret>`
- `TWILIO_PHONE_NUMBER=<secret or config value>`

Backend optional:
- `REPAIR_DESK_PASSWORD=` (reserved for external gate/password workflows)

Frontend required variables:
- `VITE_AUTH_ENABLED=true`

Frontend recommended variables:
- `VITE_API_BASE_URL=https://api.<domain>`

Never commit secrets. Store them only in hosting provider secret/environment settings.

## Render deployment env setup

Use the repository `render.yaml` blueprint to avoid manually recreating environment key names in the dashboard:

1. Commit and push repository with `render.yaml`.
2. In Render, choose `New +` -> `Blueprint` and select this repository.
3. Render creates:
   - `tech-restore-api` (backend web service)
   - `tech-restore-desk` (static frontend)
4. Provide values for each `sync: false` environment variable.
5. Deploy.

This keeps the env key structure versioned in code while still storing secrets securely in Render.

## Frontend deployment (desk.<domain>)

1. Configure frontend build env:
   - `VITE_API_BASE_URL=https://api.<domain>`
2. Build command:
   - `npm ci && npm run build`
3. Publish `frontend/dist` using your static host.
4. Bind custom domain `desk.<domain>`.
5. Put `desk.<domain>` behind Cloudflare Access policy (email allowlist, one-time PIN, IdP, etc).

## Backend deployment (api.<domain>)

Recommended first production option:
- Deploy backend as a Render Web Service (or equivalent) and mount a persistent disk.
- Keep SQLite for v1, with persistent disk + backups.

Backend start command options:
- `python run_server.py`
- or `uvicorn app.main:app --host 0.0.0.0 --port ${PORT}`

Behavior implemented:
- Production host binding uses `0.0.0.0`.
- `PORT` is used when provided.
- Local development can still run on `127.0.0.1:8787`.

## Domain and CORS configuration

1. Point `api.<domain>` to backend service.
2. Point `desk.<domain>` to frontend host.
3. Set backend `FRONTEND_ORIGIN=https://desk.<domain>`.
4. Optionally keep `TECH_RESTORE_CORS_ORIGINS` for additional allowed origins.

## Twilio production webhook configuration

Set Twilio phone number webhook URLs to:
- Voice webhook: `https://api.<domain>/api/twilio/voice`
- Recording status callback: `https://api.<domain>/api/twilio/recording`

Set backend env:
- `PUBLIC_WEBHOOK_BASE_URL=https://api.<domain>`

Twilio setup status in Settings will report URLs using this base value.

## Persistence and backups (SQLite v1 guidance)

Current persistence:
- SQLite database + local files under data/backups directories.

Required for hosted production:
- Persistent disk mounted to backend service.
- `DATABASE_URL` pointed at disk-backed path.
- Scheduled backup strategy:
  - Daily SQLite file snapshot to object storage (S3/R2/B2), plus retention policy.
  - Keep app-level export/backup feature available for manual recovery.

Required Render-safe SQLite setting:
- `DATABASE_URL=sqlite:////var/data/tech_restore_desk.sqlite`

Admin verification endpoint:
- `GET /api/system/runtime-diagnostics`
- Expected persistent-disk values in production:
   - `database_type=sqlite`
   - `database_path=/var/data/tech_restore_desk.sqlite`
   - `sqlite_under_var_data=true`
   - `persistence_status=persistent_disk`

Simplest safe first-production option:
- Render persistent disk + SQLite + automated daily file backup job.

## Validation checklist

1. Backend starts in production with `PORT` and `0.0.0.0` binding.
2. Frontend loads from `desk.<domain>` and calls `https://api.<domain>`.
3. Cloudflare Access blocks unauthenticated desk access.
4. Twilio webhook endpoints are reachable publicly.
5. In-app Twilio setup status shows:
   - `voice_webhook_url=https://api.<domain>/api/twilio/voice`
   - `recording_callback_url=https://api.<domain>/api/twilio/recording`
6. Voicemail end-to-end test:
   - place call to Twilio number
   - leave message
   - voicemail appears in inbox in desk UI
   - audio playback works
7. Confirm backups are written and restorable.
8. Confirm `GET /api/system/runtime-diagnostics` reports `/var/data/tech_restore_desk.sqlite` and `persistence_status=persistent_disk`.

## Required domain env pinning (desk + API)

To prevent browser-level `Failed to fetch` errors between desk and API domains, pin these backend env values:
- `FRONTEND_ORIGIN=https://desk.<domain>`
- `FRONTEND_BASE_URL=https://desk.<domain>`
- `PUBLIC_API_BASE_URL=https://api.<domain>`
- `PUBLIC_BASE_URL=https://api.<domain>`
- `CORS_ALLOWED_ORIGINS=https://desk.<domain>`

Frontend static env should also pin:
- `VITE_API_BASE_URL=https://api.<domain>`

Notes:
- Backend now also infers `https://desk.<domain>` from `PUBLIC_API_BASE_URL=https://api.<domain>` as a safety fallback.
- Explicit env pinning is still recommended as the primary source of truth.

## Future auth boundary (recommended next step)

Keep public webhook routes open, and add explicit backend auth boundaries for all non-webhook API routes:
- enforce JWT auth on private routes
- optionally add service token/IP allowlisting for webhook routes
- add API gateway policy at `api.<domain>` for non-Twilio routes
