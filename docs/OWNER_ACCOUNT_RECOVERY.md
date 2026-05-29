# Owner Account Recovery

A manual owner recovery script is available for emergency account restore without using invite flow.

Script:
- `backend/scripts/ensure_owner_account.py`

Run:

```bash
python -m scripts.ensure_owner_account
```

Default target account:
- email: `mattiskleinbh@gmail.com`
- password: `TR500tag`
- role: `owner`
- status: `active`

Env overrides:
- `TECH_RESTORE_OWNER_EMAIL`
- `TECH_RESTORE_OWNER_PASSWORD`
- `TECH_RESTORE_OWNER_NAME`
- `TECH_RESTORE_OWNER_USERNAME`

Security posture:
- manual-only maintenance operation
- not connected to request auth flow
- no public signup
- no auth bypass introduced

Expected success output:

```text
owner account ensured action=<created|updated> email=<masked-email> user_id=<id> db_path=<path>
```

Failure symptoms that indicate path/import context is wrong:
- `No module named scripts.ensure_owner_account`
- `No module named app`

See full report:
- `OWNER_ACCOUNT_RECOVERY_REPORT.md`
