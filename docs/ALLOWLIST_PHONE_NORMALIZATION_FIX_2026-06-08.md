# Allowlist Phone Normalization Fix

Date: 2026-06-08

## Issue

Allowlist entries created from 10-digit US inputs were saved as `+XXXXXXXXXX` instead of E.164 `+1XXXXXXXXXX`.
Twilio inbound sender values use `+1...`, so lookups could fail and trigger the blocked fallback reply.

## Fix

Updated `normalize_phone` in `backend/market_updates/allowlist.py`:
- 10-digit US numbers now normalize to `+1` prefix.
- 11-digit numbers starting with `1` normalize to `+1...`.
- Existing `+` values are preserved in normalized E.164 form.

## Validation

- Added regression test in `backend/app/tests/test_market_update_keywords.py`.
- Keyword suite passed.

## Operational repair

Re-upserted approved numbers so they are active and stored as:
- `+18483291230`
- `+19145870597`
- `+19086928547`
