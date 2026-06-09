# 2026-06-08 Allowlist Generic Message Safety Fix

Hardened allowlist matching so approved/allowlisted numbers do not fall through to blocked fallback messaging due to legacy phone-format mismatches.

Validation:
- `app/tests/test_market_update_keywords.py` passed.
