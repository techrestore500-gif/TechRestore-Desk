# Production Session / Data Persistence Audit

Date: 2026-05-29
Project: Tech Restore Desk
Scope: production-readiness audit for login/session stability, SQLite persistence, Twilio voicemail persistence, and voicemail greeting persistence after the recent auth/session/profile sweep.

## Executive Summary

This audit did not find a new frontend auth regression that would explain broad production data loss.

The strongest root-cause candidate is SQLite persistence misconfiguration in production. In the current architecture, all of the following live in the same SQLite database:
- invited users and accepted user accounts
- auth-related user records used by login and `/api/auth/me`
- Twilio settings, including `voicemail_greeting` and `voicemail_greeting_audio_url`
- voicemail inbox records

That means if production is still running with an ephemeral SQLite path such as `sqlite:///./data/tech_restore_desk.sqlite`, then a redeploy or container replacement can wipe all of those together. That matches the reported symptom pattern much better than a narrow auth bug.

A small backend addition was made during this audit:
- new admin-only endpoint: `GET /api/system/runtime-diagnostics`
- purpose: safely report the effective database type/path and whether SQLite is mounted under `/var/data`
- security: admin-only, no secrets exposed

## What Was Checked

### Session stability

Backend facts confirmed:
- JWT access tokens are issued with a 60-minute lifetime.
- Protected API routes require bearer auth except the intended public routes, including:
  - `POST /api/twilio/voice`
  - `POST /api/twilio/recording`
- `GET /api/auth/me` exists and is used to validate cached sessions.

Frontend facts confirmed:
- the app does not trust a cached token blindly
- on bootstrap, it calls `/api/auth/me` before rendering the protected shell
- API requests attach `Authorization: Bearer <token>` through the shared API client
- session clearing on `401` only happens when a token/auth header was actually present
- auth-related async page errors are normalized to a user-facing session-expired message

Conclusion:
- no new evidence of a broad token-forwarding or bootstrap bug was found
- a user can still be signed out when the JWT actually expires after 60 minutes; that is expected with the current no-refresh-token design
- the reported "session expired again" symptom is more likely to be caused by lost database state, a deployment mismatch, or a normal expired token than by a newly introduced frontend auth bug

### Database persistence

Backend facts confirmed:
- database resolution comes from `DATABASE_URL`
- Twilio settings are stored in the SQLite DB via `twilio_settings`
- voicemail inbox records are stored in the same SQLite DB via `voicemail_records`
- owner recovery script uses the same resolved DB path as the app

Implication:
- if production uses `sqlite:///./data/tech_restore_desk.sqlite`, the database is inside the service filesystem and is vulnerable to redeploy/container loss
- if production uses `sqlite:////var/data/tech_restore_desk.sqlite`, the database is on the Render persistent disk path and should survive deploys/restarts

### Voicemail persistence

Confirmed behavior:
- voicemail metadata is stored in SQLite
- actual audio is not downloaded and stored locally; playback proxies the Twilio-hosted recording URL through the backend
- if the DB row is lost, the voicemail disappears from the inbox even though Twilio may still have the audio

Implication:
- disappearing voicemail inbox entries are fully consistent with SQLite data loss
- this is not primarily a browser/session problem

### Greeting persistence

Confirmed behavior:
- greeting settings are stored in SQLite
- the public voice webhook reads current settings on each request
- the service uses DB-backed `voicemail_greeting` or `voicemail_greeting_audio_url`, with a fallback default only when DB settings are absent

Implication:
- if a custom greeting worked and later reverted or disappeared, the most likely explanation is loss of the SQLite settings row, not a cached webhook behavior bug

## Ranked Likely Causes

### 1. SQLite running on ephemeral storage in production

Likelihood: highest

Why:
- explains disappearing users, greeting settings, and voicemail records together
- matches current architecture exactly because those records share one SQLite database
- consistent with Render behavior if the DB is stored under the app filesystem instead of `/var/data`

What to verify:
- production `DATABASE_URL` must be `sqlite:////var/data/tech_restore_desk.sqlite`
- Render service must actually have a persistent disk mounted at `/var/data`
- owner/admin can call `GET /api/system/runtime-diagnostics` and confirm:
  - `database_type=sqlite`
  - `database_path=/var/data/tech_restore_desk.sqlite`
  - `sqlite_under_var_data=true`
  - `persistence_status=persistent_disk`

### 2. Frontend/backend deployment mismatch after the auth sweep

Likelihood: medium

Why:
- if only one side was redeployed, production could temporarily show stale behavior or inconsistent session handling
- this can produce confusing login/session symptoms without causing true data loss

What to verify:
- frontend and backend were both redeployed from the auth/session/profile sweep branch/commit set
- frontend points to the intended production API base URL
- backend has auth enabled with the intended secret values

### 3. Normal JWT expiry after 60 minutes with no refresh-token flow

Likelihood: medium-low

Why:
- current design intentionally expires tokens after 60 minutes
- the frontend discovers expiry on bootstrap or the next protected request and then returns the user to sign-in
- this can feel like an abrupt logout, but it does not explain missing voicemails or missing greeting settings

What to verify:
- compare the time between successful login and observed sign-out
- if roughly 60 minutes elapsed, the observed sign-out is expected behavior under the current design

### 4. Secret/config drift across deploys

Likelihood: low-medium

Why:
- changing JWT secret or auth-related env unexpectedly can invalidate existing tokens
- this explains session invalidation, but still does not explain missing voicemail records unless the DB was also lost

What to verify:
- production secret values remained stable across recent deploys
- no accidental fallback to development/default auth secrets occurred

### 5. New code bug in voicemail/greeting persistence

Likelihood: low

Why:
- current code and tests still show Twilio settings persistence, voicemail record creation, inbox retrieval, and playback proxy behavior working as designed
- no failing code path was found that would selectively erase greeting or voicemail records while leaving the rest of the DB intact

## Direct Answers

### Is the current codebase more likely suffering from a session bug or a persistence/config bug?

More likely a persistence/config bug.

### Are voicemail greetings and voicemail inbox records actually persisted today?

Yes. Both are persisted in SQLite today.

### Could the app still log a user out even if there is no new auth bug?

Yes.
- JWT expiry after 60 minutes will do that.
- Loss of the user/account DB state would also make `/api/auth/me` fail and force sign-in.
- secret drift across deploys could invalidate old tokens.

### If voicemail audio disappears from the inbox, does that prove Twilio lost the recording?

No.
The inbox record can disappear because the SQLite row is gone, even while Twilio still retains the recording audio behind the original recording SID/URL.

### What changed in code during this audit?

Added:
- `GET /api/system/runtime-diagnostics` (admin-only)

This endpoint returns only safe runtime information needed for production verification:
- database type
- effective database path
- whether `DATABASE_URL` is configured
- whether the SQLite path is under `/var/data`
- a persistence classification and warning when the path is not persistent-disk-backed

## Production Verification Checklist

1. Confirm Render backend has a persistent disk mounted at `/var/data`.
2. Confirm backend env is exactly:
   - `DATABASE_URL=sqlite:////var/data/tech_restore_desk.sqlite`
3. Confirm frontend points to the intended production API URL.
4. Redeploy both frontend and backend from the current auth/session/profile sweep state.
5. Sign in as owner/admin.
6. Call `GET /api/system/runtime-diagnostics`.
7. Confirm response indicates persistent disk.
8. Create or edit a Twilio greeting.
9. Leave a test voicemail.
10. Redeploy backend once.
11. Verify all three still remain:
   - login works for the same user
   - greeting setting still exists
   - voicemail inbox record still exists

## Validation Performed

Backend validation run after the audit change:
- `python -m pytest app/tests/test_observability_and_settings.py app/tests/test_twilio_api.py`
- result: `24 passed`

The Twilio suite continues to cover:
- Twilio settings persistence
- greeting selection behavior
- voicemail record creation
- voicemail inbox retrieval
- voicemail audio proxy behavior

## Recommended Immediate Action

Set production to persistent SQLite if it is not already there:
- `DATABASE_URL=sqlite:////var/data/tech_restore_desk.sqlite`

Then use the new admin-only runtime diagnostics endpoint to confirm production is actually reading that path after deploy.

If production is already on `/var/data` and data is still disappearing, the next investigation should focus on Render disk attachment state and deployment/environment drift rather than reopening the auth/session frontend changes first.
