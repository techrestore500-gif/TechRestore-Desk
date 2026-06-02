# Real Tech Restore Data Reset / Import Report

## What the script does

`backend/scripts/seed_real_tech_restore_data.py` creates a backup of the active SQLite database, wipes existing ticket/repair data plus existing hours/time-tracking data, preserves protected auth/settings/Twilio records, and then imports the real Tech Restore customer, repair, pricing-note, inventory-note, and Mattis time records provided for this system.

## What tables are deleted or wiped

- `repair_tickets`
- `ticket_status_history`
- `ticket_notes`
- `repair_actions`
- `part_usage`
- `loaner_checkouts` rows tied to deleted tickets
- `inventory_movements` rows tied to deleted tickets/repair actions
- `technician_hours`
- `technician_clock_sessions`
- `attachments` rows tied to ticket/repair-action entities
- `activity_logs` rows tied to ticket/hour/repair-action entity types

If a table does not exist in the target SQLite schema, the script skips it and reports the skip.

## What tables are intentionally not touched

- `users`
- `auth_invites`
- `pricing_defaults`
- `status_workflow_rules`
- `twilio_settings`
- `voicemail_records` rows are preserved; only `ticket_id` links are cleared when they point at deleted tickets
- app configuration and other non-ticket/non-hours tables
- inventory stock tables (`parts`, `donor_devices`) are preserved

## Backup behavior and backup path format

The script uses the app's existing backup helper before making changes. Backup files are created under the backend backups directory using this format:

- `backups/backup-<ISO_TIMESTAMP>.sqlite`

The script prints the exact backup path before reporting the import summary.

## Real customers inserted or updated

- Yossi Weiss
- Yossi Toder
- Ungar
- Unknown Screen Customer

The script tries to avoid duplicate customer creation by matching on phone first when available, then by customer name.

## Real tickets / repairs inserted

- 2026-05-07: Yossi Weiss, Wonder phone, touchpad replacement, standard price $35, actual charge $25, unpaid, completed
- 2026-05-13: Yossi Toder, Alcatel 4044T, SIM card not reading, no charge, customer declined repair
- 2026-06-02: Ungar, Kyocera E4810, white screen, normal price $85, actual charge $0 on the house, completed
- 2026-05-25: Unknown Screen Customer, Samsung Galaxy A13 5G / SM-A136U1, screen repair estimate, customer declined

## Real hours inserted

- Mattis at $20/hour
- 10 hour records inserted
- Total time = 14.00 hours
- Total value = $280.00

## Pricing notes added or skipped

Added as ticket-level `pricing` and `internal` notes because the app does not have a dedicated global pricing-rules table for this specific business guidance.

Included:

- E4810 white-screen `$85` screen-only rule
- E4810 `$120` shell/MBS swap rule
- no diagnosis charge wording
- customer-facing quote text
- Yossi Weiss standard `$35` vs actual `$25` unpaid note

## Inventory notes added or skipped

Added as an idempotent `inventory_purchases` record with three `inventory_purchase_items` rows using reference number `TR-REAL-STOCK-20260513`.

Included:

- 6 Kyocera E4610 @ $90
- 3 Kyocera E4810 @ $60
- 2 LG Classic @ $25
- total cost $770

## Exact command to run in Render One-Off Job

`python scripts/seed_real_tech_restore_data.py`

## Exact command to run in Render Shell

`cd /app && python scripts/seed_real_tech_restore_data.py`

## Local / test validation performed

- Added focused pytest coverage in `backend/app/tests/test_seed_real_tech_restore_data.py`
- Verified demo ticket/hour data is replaced with only the real records
- Verified hour total is 14.00 and computed value is $280.00
- Verified Yossi Weiss remains `$25` unpaid with `$35` standard price preserved in notes
- Verified Ungar remains `$0` / on the house with `$85` standard price preserved in notes
- Verified Yossi Toder remains declined / no charge
- Verified Unknown Screen Customer keeps phone `732-237-4070` and Samsung A13 5G / SM-A136U1 identification
- Verified users, Twilio settings, pricing defaults, and workflow rules remain intact

## Production safety notes

- The script fails immediately if `DATABASE_URL` is non-SQLite
- The script fails if the resolved SQLite database file does not already exist
- The script warns if the resolved SQLite path does not look like Render persistent disk storage
- The script creates a backup before modifying data
- The script runs inside a transaction and rolls back on validation failure
- The script does not print passwords, invite tokens, Twilio secrets, or auth hashes

## Manual verification checklist

- Login still works
- Settings still exist
- Twilio greeting/settings still exist
- Tickets page shows only the real repair records
- Hours page shows only the real hours
- Hours total equals 14 hr 00 min
- Yossi Weiss shows $25 unpaid
- Ungar shows $0/on the house
- Yossi Toder shows declined/no repair
- Samsung A13 screen customer shows canceled/declined behavior via Customer Declined status and notes
- No fake/test ticket data remains
- No fake/test hour data remains