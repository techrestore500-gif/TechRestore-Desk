# 2026-06-16 - Real Tech Restore Seed Data and Balance Fix

## Summary

Centralized the real Tech Restore customer/job dataset into a shared backend seed module, then wired both the database bootstrap path and the reset/import script to that source so the real data loads idempotently.

Updated dashboard and tickets balance summaries so only completed unpaid jobs count as owed balances. Open jobs and already-paid jobs no longer inflate unpaid counts.

## Validation

- Backend seed/import test passes
- Frontend dashboard and tickets balance tests pass

## Notes

- Protected auth/settings/Twilio data remains untouched during reset/import
- The seed data now loads without duplicating repair tickets on repeat import
- The real seed dataset contains 9 customers and 11 total repair jobs
