# 2026-05-29 Owner Account Recovery Script

## Added

- `backend/scripts/ensure_owner_account.py`

## Purpose

Manual emergency seed/recovery of an owner account via operator command in Render Shell or One-Off Job.

## Inputs

Env vars (optional):
- `TECH_RESTORE_OWNER_EMAIL`
- `TECH_RESTORE_OWNER_PASSWORD`
- `TECH_RESTORE_OWNER_NAME`
- `TECH_RESTORE_OWNER_USERNAME`

Defaults:
- email `mattiskleinbh@gmail.com`
- password `TR500tag`
- name `Mattis Klein`
- username `techrestoreowner`

## Behavior

- create owner if missing
- update existing email account to owner/active and reset password
- prevent duplicate by email
- safe output only (no password/hash)

## Command

```bash
python -m scripts.ensure_owner_account
```

Render backend service has `rootDir: backend`, so command context already starts in backend.
