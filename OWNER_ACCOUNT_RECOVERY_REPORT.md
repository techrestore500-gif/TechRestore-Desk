# OWNER_ACCOUNT_RECOVERY_REPORT

## What Was Added

A manual maintenance/recovery script was added:
- `backend/scripts/ensure_owner_account.py`

This script ensures exactly one owner account for a configured email. It can:
- create the owner account if missing
- update an existing account (same email) to owner/active and reset password

Defaults:
- `TECH_RESTORE_OWNER_EMAIL=mattiskleinbh@gmail.com`
- `TECH_RESTORE_OWNER_PASSWORD=TR500tag`
- `TECH_RESTORE_OWNER_NAME=Mattis Klein`
- `TECH_RESTORE_OWNER_USERNAME=techrestoreowner`

Optional env overrides:
- `TECH_RESTORE_OWNER_EMAIL`
- `TECH_RESTORE_OWNER_PASSWORD`
- `TECH_RESTORE_OWNER_NAME`
- `TECH_RESTORE_OWNER_USERNAME`

## Why This Is Not a Bypass/Backdoor

- The script is not wired into request handlers, login flow, middleware, or runtime auth decisions.
- No changes were made to `POST /api/auth/login` behavior to allow hidden credentials.
- No public signup route was added.
- JWT/session enforcement remains unchanged.
- Protected routes remain protected.
- Twilio public webhook routes remain unauthenticated as before.

This is strictly an operator-triggered maintenance command run manually from Render Shell or a Render One-Off Job.

## Database + Hashing Safety

- Uses app database connection utilities (`app.database.get_connection`) so it targets the same DB resolution path used by the app (`DATABASE_URL`-driven behavior).
- Uses existing password hashing utility (`app.utils.passwords.hash_password`).
- Does not print password or password hash.
- Prints safe summary only (action, masked email, user id, db path).

## Behavior Details

If owner email does not exist:
- creates user with:
  - name from env/default
  - email normalized (trim + lowercase)
  - username from env/default
  - role `owner`
  - status `active`
  - `is_active = 1`
  - password hash from configured password

If owner email exists:
- updates:
  - password hash
  - role = `owner`
  - status = `active`
  - is_active = `1`
- no duplicate user creation

## Exact Render Commands

### Render One-Off Job Command

Run from repo root service command:

```bash
cd backend && python -m scripts.ensure_owner_account
```

### Render Shell Command

In shell at repo root:

```bash
cd backend
python -m scripts.ensure_owner_account
```

Optional env override example:

```bash
TECH_RESTORE_OWNER_EMAIL=mattiskleinbh@gmail.com TECH_RESTORE_OWNER_PASSWORD=TR500tag cd backend && python -m scripts.ensure_owner_account
```

## Tests Added/Run

Added tests:
- `backend/app/tests/test_owner_recovery_script.py`
  - creates owner when missing
  - updates existing user without duplicate
  - seeded owner logs in with normal `POST /api/auth/login`
  - wrong password fails
  - role/status/is_active are correct

Executed:

```bash
pytest app/tests/test_owner_recovery_script.py app/tests/test_auth_api.py app/tests/test_twilio_api.py
```

Result:
- `46 passed`

## Security Notes

- No auth bypass path added.
- No public signup added.
- No weakening of JWT/session behavior.
- No Twilio public route auth changes.
- No password/hash logging.
- Recovery action is explicit and operator-triggered.

## Post-Recovery Reminder

After using this recovery seed:
1. Sign in as owner using the seeded credentials.
2. Immediately change the password from Account/Profile (`/account`).
