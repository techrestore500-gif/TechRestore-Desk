# Voicemail Compact Row + Vertical Ellipsis Report

## 1. Root Cause Of Unknown Numbers

The voicemail backend already had the correct core mapping:
- caller_number from From or Caller
- called_number from To or Called

The Unknown display came from two practical cases:
- Legacy voicemail records were created earlier with null caller/called values.
- Callback values can arrive blank/whitespace, and called line can be missing in some callback payloads.

### Fix Applied

The recording callback parser was hardened to:
- trim Twilio field values
- ignore blank strings
- map caller_number from From -> Caller fallback
- map called_number from To -> Called fallback
- fallback called_number to configured Twilio line when callback line is missing

This improves new voicemail metadata capture while keeping old null records safe.

## 2. Old Messages Vs New Messages

- Old records with null caller_number/called_number remain unchanged and show Unknown.
- New incoming voicemail records now use trimmed/fallback callback parsing and should show caller and called line when Twilio provides values, with line fallback to configured phone number when callback line is missing.

## 3. Backend Data/API Changes

No auth model changes and no credential exposure changes.

### Callback input coverage
`POST /api/twilio/recording` now explicitly accepts AccountSid input in route parsing (for field coverage/inspection), while keeping existing fields.

### Saved mapping behavior
- caller_number = first non-empty of From, Caller, caller_number
- called_number = first non-empty of To, Called, called_number, configured phone number, env phone number

### API response coverage
`GET /api/voicemails` already returned caller_number and called_number via VoicemailRecordResponse. That contract remains intact.

Public routes remain public:
- POST /api/twilio/voice
- POST /api/twilio/recording

Admin voicemail routes remain protected.

## 4. Frontend Layout Changes

Voicemail inbox was converted from large card blocks to compact inbox-like rows.

### Collapsed row now shows
- status badge
- From phone
- Line phone
- Received timestamp
- Duration
- Play button
- vertical ellipsis actions button (⋮)

### Expanded details area
Shown only for expanded row:
- audio player
- playback loading/error/retry state
- note history block
- note editor (when Add/Edit note is selected)

Only one row is expanded at a time.

## 5. Vertical Ellipsis Menu Behavior

Each row has a right-aligned vertical ellipsis button using the required icon:
- ⋮

No horizontal ellipsis is used.

Menu actions:
- Mark listened
- Mark done
- Add/Edit note (or Add note)
- Copy caller number
- Delete (destructive styling + separated)

Copy caller number is disabled when caller number is unknown.

## 6. Files Changed

- backend/app/services/twilio.py
- backend/app/routes/twilio_public.py
- backend/app/tests/test_twilio_api.py
- frontend/src/pages/VoicemailPage.tsx
- frontend/src/pages/VoicemailPage.test.tsx
- VOICEMAIL_COMPACT_ROW_VERTICAL_ELLIPSIS_REPORT.md

## 7. Tests And Build Run

Backend:
- python -m pytest app/tests/test_twilio_api.py -q
- Result: 19 passed

Frontend tests:
- npm test -- --run src/pages/VoicemailPage.test.tsx
- Result: 2 passed

Frontend build:
- npm run build
- Result: success

## 8. Deploy Order

1. Deploy backend first (callback parsing hardening for caller/line metadata).
2. Deploy frontend second (compact row inbox and ⋮ actions menu).
3. Place a new voicemail test call and verify From/Line are shown.

## 9. Manual Production Verification Steps

1. Open voicemail inbox page.
2. Confirm rows are compact and multiple messages fit on-screen.
3. Confirm each row shows:
   - status
   - From: value or Unknown
   - Line: value or Unknown
   - Received
   - Duration
   - Play
   - ⋮ menu button
4. Open ⋮ menu and verify actions listed.
5. Verify Copy caller number is disabled when caller is Unknown.
6. Click Play and confirm row expands and audio playback works.
7. Use Add/Edit note from ⋮, save note, confirm note is retained.
8. Verify Mark listened and Mark done still update status.
9. Verify Delete still asks for confirmation and removes voicemail.
10. Place a fresh inbound voicemail call and confirm new row shows caller and line values when Twilio provides metadata.
