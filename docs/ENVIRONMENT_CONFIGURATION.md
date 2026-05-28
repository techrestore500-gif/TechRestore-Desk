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
- ADMIN_INVITE_BOOTSTRAP_KEY
- DATABASE_URL
- SECRET_KEY
- FRONTEND_BASE_URL
- CORS_ALLOWED_ORIGINS

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

## Required vs Optional Summary

Backend required (core app):
- PYTHON_VERSION
- REPAIR_DESK_AUTH_ENABLED
- ADMIN_EMAIL
- ADMIN_INVITE_BOOTSTRAP
- ADMIN_INVITE_BOOTSTRAP_KEY
- DATABASE_URL
- SECRET_KEY
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
- First admin/owner bootstrap sends an emailed invite at startup when no users exist and `ADMIN_INVITE_BOOTSTRAP=true`.
- Emergency bootstrap resend endpoint exists at `POST /api/auth/bootstrap/resend` and requires `X-Bootstrap-Key` matching `ADMIN_INVITE_BOOTSTRAP_KEY`.

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
