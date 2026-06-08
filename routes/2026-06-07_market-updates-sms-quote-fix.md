# 2026-06-07 Market Updates SMS Quote Fix

The market updates SMS feature was returning `unavailable` because the `yfinance` history/fast_info path was failing under the current Python environment's SSL/network behavior.

The fix was to switch the quote fetch to Yahoo Finance's chart JSON endpoint and keep `yfinance` only as a fallback. This restored real values for BTC, S&P 500, and Nasdaq SMS replies without changing the existing inbound keyword flow.

Validation:
- `HELP` and `CHECK` still reply correctly.
- `BTC` now returns a real price sentence.
- Targeted tests passed after the change.
