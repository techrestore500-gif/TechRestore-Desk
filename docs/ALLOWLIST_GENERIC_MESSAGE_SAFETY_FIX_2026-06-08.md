# Allowlist Generic Message Safety Fix

Date: 2026-06-08

## Goal

Ensure allowlisted numbers never receive the blocked fallback SMS that tells callers to call and leave a message.

## Root cause

Some legacy allowlist records were stored in a non-standard format (`+XXXXXXXXXX`) while current normalization uses E.164-like `+1XXXXXXXXXX` for US numbers. Matching could fail if inbound and stored formats differed.

## Fix

Updated allowlist matching logic to check both canonical and legacy-compatible candidate formats when evaluating inbound sender numbers.

## Files

- `backend/market_updates/allowlist.py`
- `backend/app/tests/test_market_update_keywords.py`

## Validation

- Added regression test for legacy-format allowlist entry matching.
- Market keyword test suite passed.
