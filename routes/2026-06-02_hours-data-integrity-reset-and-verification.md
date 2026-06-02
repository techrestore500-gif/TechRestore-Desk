# 2026-06-02 - Hours Data Integrity Reset And Verification

## Goal

Resolve the reported `43:10` day/month totals on the Hours calendar and ensure calendar totals, selected-day totals, and day history are trustworthy.

## Investigation Summary

- Audited `technician_hours` in local DB (`data/tech_restore_desk.sqlite`) for anomalous rows and oversized values.
- Verified frontend grouping logic is based on `work_date` (not `created_at`), with selected-day filtering and calendar-day aggregation also using normalized `work_date`.
- Verified UI formatter maps decimal hours to `H:MM` consistently.

## Root Cause

The `43:10` value is a **data integrity symptom** (hours row values in storage), not a remaining calendar math bug in current code.

Current code path is unit-consistent:
- UI manual entry is minutes.
- Frontend converts `minutes / 60` for API payload.
- Backend stores decimal hours in `hours_worked`.
- UI displays decimal hours as `H:MM`.

If a bad row like `43.1667` exists, the UI will correctly render `43:10`.

## Corrective Action Taken

- Executed safe reset/import script to remove stale test/bad rows and reinsert the known real Tech Restore dataset:
  - `python -m scripts.seed_real_tech_restore_data`
- Backup created before reset:
  - `backups/backup-2026-06-02T22-22-01.699138+00-00.sqlite`

## Post-Reset Verified Totals

- 2026-05-07: 1:30
- 2026-05-10: 3:20
- 2026-05-13: 0:30
- 2026-05-14: 0:30
- 2026-05-24: 1:00
- 2026-05-25: 1:10
- 2026-05-26: 2:00
- 2026-05-27: 1:20
- 2026-06-01: 1:40
- 2026-06-02: 1:00
- June month total: 2:40
- Grand total: 14:00

## Validation Run

- Frontend build: pass (`npm run build`)
- Backend Hours-focused tests: pass (`python -m pytest app/tests/test_api.py -k Hours`)

## Notes

- Day totals are grouped by `work_date` (actual work day), not log timestamp.
- An entry logged today for work done on a prior day will appear under the prior day’s `work_date`.
