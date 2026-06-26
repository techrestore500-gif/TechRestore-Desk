# Active Users Authoritative Data Source Fix (2026-06-26)

## Problem

Team Access incorrectly treated accepted invites as active users. This caused drift between invitation history and actual account state.

## Fix

- Added frontend users API fetch helper for GET /api/auth/users.
- Updated Team Access page to use two authoritative datasets:
  - Current users: sourced from users endpoint, filtered to active and enabled accounts.
  - Invites: sourced from invites endpoint, split into pending invites and invite history.
- Updated Team Access filter controls to:
  - Current users
  - Pending invites
  - Invite history
- Kept invite actions (create/resend/revoke) scoped to invite datasets and invite-only refresh.

## Behavioral outcomes

- Directly created users now appear under Current users.
- Disabled/deleted users are not shown as current active users.
- Accepted invites are represented as invitation history, not active users.
- Owner-only access boundaries for Team Access remain unchanged.

## Validation

- Targeted Team Access frontend tests: pass.
- Full frontend test suite: pass.
- Frontend production build: pass.
- Full backend test suite: pass.
