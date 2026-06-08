# Market Updates Blocked Number Message (Tech Restore Only)

Date: 2026-06-08

## Change

Updated the blocked-number SMS response to remove market-specific language and keep messaging focused only on Tech Restore support instructions.

Current response intent:
- Thank the sender for contacting Tech Restore
- Explain that this line is not enabled for text support
- Ask them to call Tech Restore to leave a message
- Provide immediate support number: 8483291230 (call/text)
- Keep REQUEST flow available for access updates

## Files

- `backend/market_updates/keyword_handlers.py`
- `backend/app/tests/test_market_update_keywords.py`

## Validation

- Keyword test suite passed for this behavior.
