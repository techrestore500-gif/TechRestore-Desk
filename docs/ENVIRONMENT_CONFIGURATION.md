# Environment Configuration

This document defines local and production environment variable setup for Tech Restore Desk, including Render deployment.

## Local Dev Environment

Backend local dev defaults work without setting most production variables.

Typical local backend values:
- APP_ENV=development
- REPAIR_DESK_AUTH_ENABLED=false
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
- DATABASE_URL
- SECRET_KEY
- PUBLIC_BASE_URL
- CORS_ALLOWED_ORIGINS

Required for Twilio voicemail:
- TWILIO_ACCOUNT_SID
- TWILIO_AUTH_TOKEN
- TWILIO_PHONE_NUMBER

Optional:
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
- DATABASE_URL
- SECRET_KEY
- PUBLIC_BASE_URL
- CORS_ALLOWED_ORIGINS

Backend required (voicemail):
- TWILIO_ACCOUNT_SID
- TWILIO_AUTH_TOKEN
- TWILIO_PHONE_NUMBER

Backend optional:
- REPAIR_DESK_PASSWORD

Frontend required:
- VITE_AUTH_ENABLED

Frontend conditionally required:
- VITE_API_BASE_URL (recommended explicit value in production)
