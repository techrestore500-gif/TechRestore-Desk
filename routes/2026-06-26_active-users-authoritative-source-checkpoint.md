# 2026-06-26 Active Users Authoritative Source Checkpoint

## Delivered

- Team Access Active Users view no longer derives from accepted invites.
- Current users now come from /api/auth/users as the single source of truth.
- Invite data remains available as:
  - Pending invites
  - Invite history
- Invite actions refresh invite datasets without coupling to user listing behavior.

## Access-control integrity

- Owner-only guard on Team Access remains in place.
- Admin invite role limits remain unchanged in invite flow.

## Verification

- Targeted Team Access tests: pass.
- Frontend full test suite: pass.
- Frontend build: pass.
- Backend full test suite: pass.
