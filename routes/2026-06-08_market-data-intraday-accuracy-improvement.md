# 2026-06-08 Market Data Intraday Accuracy Improvement

Adjusted market quote retrieval to prefer intraday Yahoo chart prices over daily candle-only values for current SMS quote responses.

Validation:
- `app/tests/test_market_updates.py` passed.
