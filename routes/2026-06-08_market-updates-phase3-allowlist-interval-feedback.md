# 2026-06-08 Market Updates Phase 3

Implemented additional requested capabilities:

- Inbound number allowlist enforcement.
- Invite request drafting for blocked numbers through SMS request keywords.
- Admin APIs for allowlist and invite request management.
- Interval reminder scheduling every N minutes (min 30) with start and stop datetime.
- Feedback keyword persistence and admin feedback listing endpoint.
- New feedback portal service scaffold for separate deployment target (`feedback.techrestoredesk.com`).

Regression status:
- Focused backend tests passed, including Twilio-related suites.
