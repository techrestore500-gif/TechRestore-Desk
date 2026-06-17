# 2026-06-16 Seed Ticket Number Normalization

Normalized imported real-data ticket numbers from legacy `TR-REAL-*` values to standard `TR-xxxxx` values.

## Notes
- Shared real-data sync now upgrades existing legacy seeded tickets in place.
- Future operational syncs and reset imports keep standard ticket numbering.
- Added regression coverage to ensure seeded tickets no longer retain `TR-REAL-*` numbers.
