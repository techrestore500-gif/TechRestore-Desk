# Auth Invite / Login Bug Report

**Date:** 2026-05-28  
**Severity:** Critical (production owner account locked out)  
**Status:** Patched and tested  

---

## Root Cause

In `backend/app/services/auth.py`, the `AuthService.login()` method evaluated `REPAIR_DESK_AUTH_ENABLED` and `REPAIR_DESK_PASSWORD` **before** looking up any user in the database:

```python
# BEFORE (broken)
if shared_auth_enabled and shared_password:
    if password != shared_password:
        raise ValueError("Invalid credentials")   # <-- always returned here
    ...
    return user, token, expires_at  # <-- never reached the DB lookup below

user = AuthRepository.get_user_by_email(normalized_email)  # <-- never ran
```

In production on Render:
- `REPAIR_DESK_AUTH_ENABLED=true` is declared in `render.yaml` and is active.
- `REPAIR_DESK_PASSWORD` is set in the Render dashboard as a non-empty string.

When both are set, every login attempt was compared to the shared password before ever touching the `users` table. An invite-accepted user with their own PBKDF2-hashed password was never consulted. Login with anything other than the shared password returned `HTTP 401 Invalid credentials`.

**Why the bug was invisible in local tests:** the existing test `test_invite_acceptance_activates_user_and_allows_login` only sets `TECH_RESTORE_AUTH_BYPASS=0`. It never sets `REPAIR_DESK_AUTH_ENABLED` or `REPAIR_DESK_PASSWORD`, so the shared-password branch was never entered and the bug did not surface.

---

## Answers to Investigation Questions

1. **What exact JSON does the frontend send when accepting an invite?**  
   `POST /api/auth/invites/{token}/accept` with body `{"password": "<user-chosen-password>"}`. Confirmed in `InviteAcceptPage.tsx` and `api/auth.ts`.

2. **What exact schema does the backend accept endpoint expect?**  
   `AuthInviteAcceptRequest` — a Pydantic model with a single `password: str` field. Correct and symmetric.

3. **Does the backend hash the accepted password before storing it?**  
   Yes. `accept_invite()` in `services/auth.py` calls `hash_password(password)` (PBKDF2-HMAC-SHA256 with a per-user random salt) and stores the result as `password_hash`. This was working correctly.

4. **Does login verify the password using the same hash format?**  
   Yes. `verify_password(password, stored_hash)` in `utils/passwords.py` uses the same algorithm. The hashing and verification implementations were correct. The bug was in the *routing* logic — the hash check was never reached.

5. **Is login looking up the user by the same email field that invite acceptance stores?**  
   Yes. Invite acceptance stores `invite["email"]` (already normalised to lowercase). Login calls `_validate_email()` which also lowercases the input, then `AuthRepository.get_user_by_email()` with a `LOWER(email)` index comparison. Correct.

6. **Is invite acceptance creating the user as active?**  
   Yes. `AuthRepository.create_user(status="active")` is called, which sets `is_active=1` and `approved_at=now`. Correct.

7. **Is invite acceptance storing password_hash in the correct column?**  
   Yes. The `password_hash` column is written by the `INSERT INTO users` statement in `AuthRepository.create_user()`. Correct.

8. **Is the login response 401 because user is missing, inactive, or password verification failed?**  
   Because of the shared-password early-return bug, the failure reason was effectively "wrong shared password" — not any database state issue. After the fix, distinct reasons are now logged: `user_not_found`, `account_pending`, `account_denied`, `account_disabled`, `no_role_assigned`, `account_inactive`, `wrong_password`.

9. **Safe logging without exposing credentials?**  
   Added `_log_login_failure(email, reason)` which logs only the email domain (everything after `@`) and the reason code. No email address, password, or hash is ever logged.

---

## Files Changed

| File | Change |
|---|---|
| `backend/app/services/auth.py` | Fixed `login()` priority order; added `_log_login_failure()` helper; added `import logging` |
| `backend/app/tests/test_auth_api.py` | Added 6 new tests (see below) |

No frontend changes were required. The bug was entirely in the backend login path.

---

## Exact Fix

**`backend/app/services/auth.py`** — the `login()` method was rewritten to always try per-user auth first:

```python
# AFTER (fixed)
user = AuthRepository.get_user_by_email(normalized_email)
if user is None:
    # No per-user account — shared-password is only a fallback here
    if shared_auth_enabled and shared_password and password == shared_password:
        ...
        return shared_user, token, expires_at
    _log_login_failure(normalized_email, "user_not_found")
    raise ValueError("Invalid credentials")

# Per-user account found: validate with their stored hash
...
if not verify_password(password, user["password_hash"]):
    _log_login_failure(normalized_email, "wrong_password")
    raise ValueError("Invalid credentials")

token, expires_at = create_access_token(...)
return user, token, expires_at
```

Shared-password mode still works for the no-user-exists bootstrap scenario. Once an invite-accepted user exists in the DB for that email, their own password governs login. The shared password is no longer a system-wide override.

---

## Tests Added / Updated

All tests in `backend/app/tests/test_auth_api.py`. 6 new tests appended:

| Test | Covers |
|---|---|
| `test_invite_accepted_owner_can_login_when_shared_password_also_set` | **The exact production bug** — invite accepted, `REPAIR_DESK_AUTH_ENABLED=true` + `REPAIR_DESK_PASSWORD` set, login with invite password must succeed |
| `test_invite_accepted_user_wrong_password_returns_401_when_shared_password_set` | Wrong per-user password still returns 401 even with shared password active |
| `test_shared_password_fallback_still_works_when_no_per_user_account` | Shared-password fallback regression — must still work when no DB user exists |
| `test_invite_accept_creates_active_owner_user` | Invite accept produces `status=active`, `is_active=True`, `role=owner` |
| `test_accepted_invite_is_single_use_even_after_login` | Token cannot be reused after successful accept + login |
| `test_login_email_is_case_insensitive` | Email case normalisation works end-to-end |

**Test results:** 27 passed, 0 failed, 214 warnings (Python deprecation warnings unrelated to this fix).

---

## Commands Run

```powershell
# Run full auth test suite
Set-Location 'c:/Users/owner/Desktop/Tech Restore/tech-restore-desk/backend'
python -m pytest app/tests/test_auth_api.py -v
# Result: 27 passed, 0 failed
```

No frontend changes were made, so no frontend build was required.

---

## Deploy Order

1. **Commit and push this branch to `main`.** Render will auto-deploy the backend.
2. Wait for the Render backend service to show "Deploy live" in the Events tab.
3. **No database migration required.** The fix is entirely in Python application logic — no schema changes.
4. **No frontend redeploy required.** The frontend code was correct; the bug was in the backend.

---

## Manual Production Steps After Deploy

1. **Trigger bootstrap resend** (because previous invites may have accumulated, and the old shared-password user had ID=0 with no DB record):

   ```powershell
   Invoke-RestMethod `
     -Uri "https://api.techrestoredesk.com/api/auth/bootstrap/resend" `
     -Method POST `
     -Headers @{ "X-Bootstrap-Key" = "<ADMIN_INVITE_BOOTSTRAP_KEY>" }
   ```

   This revokes any stale pending invite and sends a fresh one to `ADMIN_EMAIL`.

2. **Click the new invite link** in the email at `mattiskleinbh@gmail.com`.

3. **Set your password** on the invite accept page at `https://desk.techrestoredesk.com/invite/<token>`.

4. **Log in** with `mattiskleinbh@gmail.com` and the password you just set. This must now succeed with HTTP 200.

5. **Optional: remove `REPAIR_DESK_PASSWORD`** from Render env vars once you have confirmed login works with the per-user account. The shared password is no longer needed and reduces the attack surface.

---

## Notes

- The password hashing implementation (`utils/passwords.py`) was correct throughout — PBKDF2-HMAC-SHA256 with a 16-byte random salt and 120,000 iterations stored as `salt_hex:digest_hex`. No changes were needed there.
- The invite acceptance flow (`accept_invite()` in `services/auth.py`) was also correct throughout. It hashed and stored the password correctly.
- The `AuthRepository.create_user()` was also correct — it set `status="active"`, `is_active=1`, and the correct `password_hash`.
- The **only** broken component was the `login()` routing logic that short-circuited to shared-password mode before reaching the DB.
