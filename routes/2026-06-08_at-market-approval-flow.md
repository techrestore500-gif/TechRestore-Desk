# 2026-06-08 @MARKET Approval Flow

Implemented:
- Blocked users can request access by sending `@MARKET`.
- Approver receives SMS request and can approve by replying `YES <id>`.
- Approved requester is auto-added to allowlist and notified.
- Added `PENDING` approver command.
- Preserved Tech Restore-only wording for generic blocked responses.

Validation:
- Market keyword tests passed.
