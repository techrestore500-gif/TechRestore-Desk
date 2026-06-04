# 2026-06-04 - Voicemail caller ID and SMS alerts

## Request
- Show the incoming caller number in voicemail inbox records.
- Send an SMS alert to 848-329-1230 for each new voicemail.

## Implemented
- Added voice-call context memory from the `/api/twilio/voice` webhook so `CallSid` can later enrich `/api/twilio/recording` when Twilio omits `From`/`To` fields.
- Added caller/line fallback enrichment in voicemail recording processing:
  - Uses normalized `From` / `Caller` and `To` / `Called` values.
  - Falls back to stored voice-call context by `CallSid`.
  - Falls back to Twilio Call API lookup by `CallSid` when needed and credentials are configured.
- Added SMS notification send for newly created voicemail records only.
  - Destination defaults to `+18483291230`.
  - Supports env override through `TWILIO_NEW_VOICEMAIL_ALERT_TO`.
  - Prevents duplicate alert sends when Twilio posts updates for an existing `RecordingSid`.

## Files changed
- backend/app/services/twilio.py
- backend/app/routes/twilio_public.py
- backend/app/tests/test_twilio_api.py
- backend/.env.example

## Validation
- Ran backend tests: `app/tests/test_twilio_api.py`
- Result: 22 passed
