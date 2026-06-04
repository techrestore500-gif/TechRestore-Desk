# Voicemail caller ID and alerting update (2026-06-04)

## Summary
This update improves voicemail intake reliability and adds immediate operator alerting:

- Caller numbers are now recovered more reliably when Twilio recording callbacks arrive with missing or unknown caller fields.
- A new SMS alert is sent for each newly created voicemail to the owner alert line.

## Caller number reliability
Voicemail callback processing now resolves caller and line values in this order:

1. Twilio recording callback fields (`From`/`Caller`, `To`/`Called`)
2. Recently captured voice webhook call context by `CallSid`
3. Twilio Call API lookup by `CallSid` (when credentials are configured)

Unknown placeholders like `unknown`, `anonymous`, or `client:unknown` are ignored during normalization.

## SMS alerting behavior
- Trigger: newly created voicemail record only
- Destination: `+18483291230` by default
- Override: set `TWILIO_NEW_VOICEMAIL_ALERT_TO`
- Duplicate prevention: alert is skipped when callback updates an existing `RecordingSid`

## Configuration
Updated `backend/.env.example` with:

- `TWILIO_NEW_VOICEMAIL_ALERT_TO=+18483291230`

## Test coverage
Added tests for:

- call-context fallback to recover caller number when recording callback omits `From`
- one-alert-per-new-recording behavior (no duplicate alert on duplicate `RecordingSid` callback)
