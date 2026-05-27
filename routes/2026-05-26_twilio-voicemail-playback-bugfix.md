# 2026-05-26 Twilio Voicemail Playback Bugfix

Fixed an end-to-end playback bug where voicemail records were present in the inbox but audio controls showed 0:00/0:00.

Root cause:
- The backend audio proxy route was returning HTTP 500 when Twilio recording fetches failed TLS certificate verification in the local environment.
- The audio element received JSON error responses instead of audio bytes, which surfaced as non-playable media in the UI.

Fix summary:
- Hardened Twilio audio proxy error handling to return actionable errors instead of generic internal errors.
- Added a certificate-failure retry path for Twilio recording fetches using a non-verified TLS call only as a fallback.
- Kept Twilio credentials backend-only and continued serving playback through `/api/voicemails/{id}/audio`.
- Added callback parsing fallback for `Caller` and `Called` when `From` and `To` are missing in recording callbacks.
- Added backend tests for audio proxy success/error mapping and callback field fallback.
- Added frontend test assertion that the audio source uses the backend proxy route.

Validation:
- Backend Twilio tests: pass.
- Frontend voicemail/settings/intake targeted tests: pass.
- Live check: `/api/voicemails/{id}/audio` returns `200`, `audio/mpeg`, and non-zero byte payload.
