# Environment Configuration

This document defines local and production environment variable setup for Tech Restore Desk, including Render deployment.

## Local Dev Environment

Backend local dev defaults work without setting most production variables.

Typical local backend values:
- APP_ENV=development
- REPAIR_DESK_AUTH_ENABLED=true
- ADMIN_EMAIL=owner@example.com
- ADMIN_NAME=Tech Restore Owner
- ADMIN_INVITE_BOOTSTRAP=true
- ADMIN_INVITE_BOOTSTRAP_AUTOSEND=false
- ADMIN_INVITE_ROLE=owner
- ADMIN_INVITE_BOOTSTRAP_KEY=local-bootstrap-key
- DATABASE_URL=./data/tech_restore_desk.sqlite
- CORS_ALLOWED_ORIGINS=http://127.0.0.1:6173,http://localhost:6173

Typical local frontend values:
- VITE_API_BASE_URL=http://127.0.0.1:8787
- VITE_AUTH_ENABLED=true

If VITE_API_BASE_URL is not set, frontend auto-detects:
- development mode: http://127.0.0.1:8787
- production mode: inferred from desk.<domain> to api.<domain> when possible

## Production Environment

Copy from templates:
- backend/.env.example
- frontend/.env.example

Do not commit real .env files.

### Backend Variables

Required:
- PYTHON_VERSION
- REPAIR_DESK_AUTH_ENABLED
- ADMIN_EMAIL
- ADMIN_INVITE_BOOTSTRAP
- ADMIN_INVITE_BOOTSTRAP_AUTOSEND
- ADMIN_INVITE_BOOTSTRAP_KEY
- DATABASE_URL
- TECH_RESTORE_JWT_SECRET
- TECH_RESTORE_SIGNED_URL_SECRET
- FRONTEND_BASE_URL
- CORS_ALLOWED_ORIGINS

Legacy compatibility (supported but not preferred):
- SECRET_KEY (used only when TECH_RESTORE_JWT_SECRET is unset)

Recommended exact Render SQLite value:
- `DATABASE_URL=sqlite:////var/data/tech_restore_desk.sqlite`

Required for Twilio voicemail:
- TWILIO_ACCOUNT_SID
- TWILIO_AUTH_TOKEN
- TWILIO_PHONE_NUMBER

Optional:
- ADMIN_NAME
- ADMIN_INVITE_ROLE
- SMTP_TIMEOUT_SECONDS
- REPAIR_DESK_PASSWORD (reserved for external gate/passcode workflows)

### Frontend Variables

Required:
- VITE_AUTH_ENABLED

Required in most deployments:
- VITE_API_BASE_URL

If VITE_API_BASE_URL is omitted in production, frontend attempts domain inference (desk -> api) and then falls back to /api.

## Render Deployment Environment Setup

Use Render Blueprint from render.yaml so service env keys are managed in version control, and only secret values are provided securely.

1. Push repository with render.yaml.
2. In Render: New + -> Blueprint.
3. Select this repository and apply blueprint.
4. Fill all env vars marked sync: false.
5. Deploy services.

Render services defined:
- tech-restore-api (Python web service)
- tech-restore-desk (static frontend)

Production persistence verification:
- Sign in as an owner/admin and call `GET /api/system/runtime-diagnostics`.
- Expected SQLite production response:
	- `database_path=/var/data/tech_restore_desk.sqlite`
	- `sqlite_under_var_data=true`
	- `persistence_status=persistent_disk`

## Required vs Optional Summary

Backend required (core app):
- PYTHON_VERSION
- REPAIR_DESK_AUTH_ENABLED
- ADMIN_EMAIL
- ADMIN_INVITE_BOOTSTRAP
- ADMIN_INVITE_BOOTSTRAP_AUTOSEND
- ADMIN_INVITE_BOOTSTRAP_KEY
- DATABASE_URL
- TECH_RESTORE_JWT_SECRET
- TECH_RESTORE_SIGNED_URL_SECRET
- FRONTEND_BASE_URL
- CORS_ALLOWED_ORIGINS

Backend required (voicemail):
- TWILIO_ACCOUNT_SID
- TWILIO_AUTH_TOKEN
- TWILIO_PHONE_NUMBER

Backend optional:
- ADMIN_NAME
- ADMIN_INVITE_ROLE
- SMTP_TIMEOUT_SECONDS
- REPAIR_DESK_PASSWORD

Frontend required:
- VITE_AUTH_ENABLED

Frontend conditionally required:
- VITE_API_BASE_URL (recommended explicit value in production)

## Authentication Notes

- Main production auth model is invite-only login (`/api/auth/login`) with admin/owner-controlled invite creation and acceptance (`/api/auth/invites/*`).
- `REPAIR_DESK_PASSWORD` remains as an optional fallback mode only. If enabled with `REPAIR_DESK_AUTH_ENABLED=true`, backend still accepts shared-password logins.
- Bootstrap invite creation is enabled by `ADMIN_INVITE_BOOTSTRAP=true` when no users/admins exist.
- Startup email delivery is controlled separately by `ADMIN_INVITE_BOOTSTRAP_AUTOSEND` (recommended `false` in production to avoid invite spam on redeploys).
- Emergency bootstrap resend endpoint exists at `POST /api/auth/bootstrap/resend` and requires `X-Bootstrap-Key` matching `ADMIN_INVITE_BOOTSTRAP_KEY`.

## JWT Secret Policy

- Production and staging reject weak or placeholder secrets at startup.
- `TECH_RESTORE_JWT_SECRET` and `TECH_RESTORE_SIGNED_URL_SECRET` must both be set to non-placeholder values with minimum length requirements.
- Secret precedence is:
	- JWT: `TECH_RESTORE_JWT_SECRET` -> `SECRET_KEY` (legacy) -> development default
	- Signed URL: `TECH_RESTORE_SIGNED_URL_SECRET` -> `TECH_RESTORE_JWT_SECRET` -> `SECRET_KEY` (legacy)
- Rotating `TECH_RESTORE_JWT_SECRET` invalidates existing bearer sessions immediately; all users must log in again after rotation.

## SMTP Configuration (Render)

Invite delivery uses environment-driven SMTP mode selection and supports both STARTTLS and SSL-on-connect.

Recommended Gmail STARTTLS (port 587):
- SMTP_HOST=smtp.gmail.com
- SMTP_PORT=587
- SMTP_USE_SSL=false
- SMTP_STARTTLS=true
- SMTP_TIMEOUT_SECONDS=20
- SMTP_USERNAME=techrestore500@gmail.com
- SMTP_PASSWORD=<gmail-app-password>
- SMTP_FROM_EMAIL=techrestore500@gmail.com
- SMTP_FROM_NAME=Tech Restore

Gmail SSL fallback (port 465):
- SMTP_HOST=smtp.gmail.com
- SMTP_PORT=465
- SMTP_USE_SSL=true
- SMTP_STARTTLS=false
- SMTP_TIMEOUT_SECONDS=20
- SMTP_USERNAME=techrestore500@gmail.com
- SMTP_PASSWORD=<gmail-app-password>
- SMTP_FROM_EMAIL=techrestore500@gmail.com
- SMTP_FROM_NAME=Tech Restore
