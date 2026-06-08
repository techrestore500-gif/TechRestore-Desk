# Market Updates @MARKET Approval Flow

Date: 2026-06-08

## Summary

Added an SMS approval workflow so blocked numbers can request access by sending `@MARKET`.

## Behavior

1. A blocked sender texts `@MARKET`.
2. The system creates/updates a pending invite request.
3. The configured approver number receives an SMS notification with request ID.
4. Approver replies `YES <id>` to approve.
5. The requester number is added to allowlist and receives approval confirmation SMS.

## Approver controls

- `YES <id>` approves the pending request by ID.
- `YES` auto-approves if exactly one request is pending.
- `PENDING` lists pending request IDs.

## Configuration

- `MARKET_ACCESS_APPROVER_NUMBER` sets the approver phone.
- Defaults to `8483291230` if not configured.

## Important note

Generic blocked-number replies remain Tech Restore-only and do not mention market.

## Files

- `backend/market_updates/keyword_handlers.py`
- `backend/app/tests/test_market_update_keywords.py`

## Validation

- Keyword tests passed including the new @MARKET approval scenarios.
