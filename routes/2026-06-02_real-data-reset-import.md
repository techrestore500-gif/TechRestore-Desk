# 2026-06-02 - Real Data Reset / Import Script

## Goal

Replace existing demo or stale ticket/hour data with the real tracked Tech Restore records while preserving auth, settings, Twilio, voicemail, and general app configuration.

## Delivered

- Added `backend/scripts/seed_real_tech_restore_data.py`
- Added safe SQLite-only backup + import flow
- Added schema-aware deletion of ticket trees and hour trees
- Added import of the four real repair records
- Added import of the ten real Mattis hours entries totaling 14.00 hours
- Added pricing/internal ticket notes for the real business context
- Added idempotent inventory purchase note for the May 13 stock acquisition
- Added focused pytest coverage for the script

## Validation

- Focused backend pytest: pass

## Notes

- Protected tables are preserved
- Voicemail rows are preserved; only deleted ticket links are nulled when necessary