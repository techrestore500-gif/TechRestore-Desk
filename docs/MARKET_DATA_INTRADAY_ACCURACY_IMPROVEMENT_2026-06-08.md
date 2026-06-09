# Market Data Intraday Accuracy Improvement

Date: 2026-06-08

## Change

Updated market quote fetching to prefer Yahoo intraday chart data (`1d` range, `1m` interval) for latest prices.
If intraday data is unavailable, the service falls back to daily chart data.

## Why

The prior implementation could mix live meta values with daily candle closes, which can be less precise for current-price SMS responses.
The new logic uses the latest intraday trade from the chart series when available, then calculates change versus previous close from Yahoo metadata.

## Files

- `backend/market_updates/market_data.py`
- `backend/app/tests/test_market_updates.py`

## Validation

- Focused market data tests passed.

## Important note

This improves quote accuracy and consistency, but it does not create a true exchange-guaranteed market data feed.
For strict real-time/exchange-grade guarantees, the app would need a licensed provider such as Polygon, IEX Cloud, Twelve Data premium, Alpaca market data, or direct exchange feeds.
