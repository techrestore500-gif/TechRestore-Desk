# Market Updates SMS Quote Fix

Date: 2026-06-07

## Summary

The market updates SMS flow now fetches live quote values from Yahoo Finance's chart endpoint instead of relying on `yfinance` history/fast_info calls, which were failing in this environment because of SSL verification issues.

## Result

- `HELP` and `CHECK` still return SMS replies as before.
- `BTC`, `SPX`, and `NASDAQ` now return actual live values instead of `unavailable`.
- The formatter continues to display a compact SMS-friendly price and percent change line.

## Validation

- Targeted market updates and Twilio regression tests passed: 48 passed.
- Live Python verification returned real values for `BTC-USD`, `^GSPC`, and `^IXIC`.
