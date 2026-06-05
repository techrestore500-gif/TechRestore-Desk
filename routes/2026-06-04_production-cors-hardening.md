# 2026-06-04 - Production CORS hardening for voicemail fetch

## Problem
Voicemail page in production showed "Failed to fetch" because browser requests to API were blocked before a readable HTTP response reached the frontend.

## Fixes applied
- Backend CORS settings now include normalized origin from:
  - `FRONTEND_ORIGIN`
  - `FRONTEND_BASE_URL`
- Backend now infers `https://desk.<domain>` automatically from `PUBLIC_API_BASE_URL=https://api.<domain>` when explicit frontend origin vars are absent.
- Render production config now pins these values instead of leaving them unmanaged:
  - `FRONTEND_ORIGIN=https://desk.techrestoredesk.com`
  - `FRONTEND_BASE_URL=https://desk.techrestoredesk.com`
  - `PUBLIC_API_BASE_URL=https://api.techrestoredesk.com`
  - `PUBLIC_BASE_URL=https://api.techrestoredesk.com`
  - `CORS_ALLOWED_ORIGINS=https://desk.techrestoredesk.com`
  - Frontend `VITE_API_BASE_URL=https://api.techrestoredesk.com`

## Files changed
- backend/app/core/settings.py
- backend/app/tests/test_observability_and_settings.py
- render.yaml

## Validation
- Backend settings tests: 10 passed
- Frontend production build: passed
