# 2026-06-08 Allowlist Phone Normalization Fix

Fixed market SMS allowlist phone normalization so 10-digit US inputs are stored as `+1...` and match Twilio inbound sender values.

Also re-upserted approved numbers as active:
- +18483291230
- +19145870597
- +19086928547

Validation:
- app/tests/test_market_update_keywords.py passed (18 tests).
