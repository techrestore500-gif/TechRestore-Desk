# Market Updates Approver Notification Reliability Fix

Date: 2026-06-08

## Issue

Approver SMS notifications for `@MARKET` requests could silently fail when `MARKET_UPDATE_TO_NUMBER(S)` was not configured, because notification sending reused `load_config()` from market send workflows.

## Fix

Approver/request notification sending now uses direct Twilio credential env vars only:
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_NUMBER` (fallback: `TWILIO_PHONE_NUMBER`)

This decouples request-approval notifications from market recipient configuration.

## Files

- `backend/market_updates/keyword_handlers.py`
- `backend/app/tests/test_market_update_keywords.py`

## Validation

- Market keyword tests passed (including @MARKET + YES approval flow).
