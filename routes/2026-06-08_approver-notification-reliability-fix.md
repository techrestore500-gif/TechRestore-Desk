# 2026-06-08 Approver Notification Reliability Fix

Updated @MARKET approver SMS notification path to rely on direct Twilio env vars instead of market-update recipient config.

Result:
- Approval request notifications are sent reliably when Twilio creds are present.

Validation:
- Keyword tests passed.
