# 2026-06-17 Raizy Krieger ticket seed/import update

## Summary
- Added a new real-data seed/import customer + job record for Raizy Krieger.
- Record details:
  - Customer: Raizy Krieger
  - Phone: 732-732-2743
  - Device: Canon SX740
  - Issue: Display issue
  - Repair summary: Display cable replacement
  - Final charge: $75.00
  - Payment status: unpaid
  - Ticket status: Ready for Pickup
  - Customer notified: Yes (captured in ticket notes/status history)
  - Intake date: 2026-06-17
- Preserved idempotency by using a deterministic canonical ticket number (`TR-00012`) plus legacy key (`TR-REAL-20260617-01`) so reruns update in place without duplicate customer/ticket creation.

## Additional behavior verification
- Updated Tickets page unpaid summary count scope to include finalized unpaid statuses: `Picked Up / Closed`, `Completed`, and `Ready for Pickup`.
- Ensures unpaid-ready-for-pickup jobs like Raizy's appear in unpaid summaries.

## Files changed
- backend/app/real_seed_data.py
- backend/scripts/seed_real_tech_restore_data.py
- backend/app/tests/test_seed_real_tech_restore_data.py
- frontend/src/pages/TicketsPage.tsx
- frontend/src/pages/TicketsPage.test.tsx
- docs/IMPLEMENTATION_STATUS.md

## Validation
- Frontend: `npm run test -- --run src/pages/TicketsPage.test.tsx`
- Backend: `python -m pytest app/tests/test_seed_real_tech_restore_data.py -q`

Both passed.
