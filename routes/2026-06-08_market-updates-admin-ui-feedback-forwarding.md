# 2026-06-08 Market Updates Admin UI and Feedback Forwarding

Delivered:
- New owner/admin desk page at `/market-updates-admin` for allowlist, invite requests, and feedback review.
- New frontend API client for market updates admin routes.
- Optional backend forwarding of SMS feedback entries to feedback portal ingest endpoint using environment-configured URL/token.
- Updated allowlist env seeding from market recipient env vars.
- Render config updated with backend ingest env vars.

Validation:
- Focused backend tests passed.
- Frontend build passed.
