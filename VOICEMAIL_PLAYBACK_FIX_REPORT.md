# Voicemail Playback Fix Report

**Date:** 2026-05-29  
**Issue:** Voicemail audio player showed "Recording is not ready yet. Try again in a few seconds." and played nothing, even for recordings with a valid duration (e.g. 0:21).

---

## Root Cause

**Primary cause — browser `<audio>` cannot send Bearer token**

The voicemail page used a standard HTML `<audio src="/api/voicemails/{id}/audio">` element. The browser makes a plain GET request for the `src` URL with no custom headers. The backend endpoint `/api/voicemails/{id}/audio` is protected by `AuthGateMiddleware`, which requires an `Authorization: Bearer <token>` header. Since the browser's audio element cannot inject that header, every request returned **HTTP 401**. The `onError` handler fired and displayed the hardcoded static string "Recording is not ready yet. Try again in a few seconds." — regardless of the real HTTP status.

**Secondary cause — misleading generic onError message**

The original `onError` handler set a single static error string for every possible failure reason (401, 404, 503, network error). This obscured the actual cause and provided no retry path for the user.

**Tertiary cause (edge case) — Twilio media availability lag**

Twilio sometimes fires the `recordingStatusCallback` before the recording media file is fully available on its servers. When the backend proxies the URL to Twilio and Twilio returns 404, the backend correctly responds with 503 ("not ready yet"), but the original UI offered no retry button.

---

## Files Changed

| File | Change |
|------|--------|
| `frontend/src/pages/VoicemailPage.tsx` | Replaced bare `<audio src="...">` with fetch-via-`apiFetch` → blob URL player. Added loading state, per-message error display, and Retry button. |
| `frontend/src/api/system.ts` | Added `fetchVoicemailAudio()` — fetches audio through the authenticated API client and returns `{ blob, contentType }`. |
| `frontend/src/pages/VoicemailPage.test.tsx` | Updated test to mock `fetchVoicemailAudio`, mock `URL.createObjectURL` / `revokeObjectURL` (absent in jsdom), assert blob URL is used. Added second test for error + Retry UI. |
| `backend/app/services/twilio.py` | Added `logger.warning()` calls around Twilio 401/403/404/other error responses in `fetch_recording_audio()`. No auth token is logged. |
| `backend/app/tests/test_twilio_api.py` | Added 4 new tests: `.mp3` extension appended, no double-append, correct content-type forwarded, 404 proxy when no recording URL. |

---

## Exact Fix

### Frontend — blob URL audio loading pattern

The `<audio>` element can no longer add a `Bearer` JWT header to its own requests. The fix fetches the audio binary through the same authenticated `apiFetch` wrapper used by all other API calls, creates a local `blob:` URL, and passes that as the `<audio>` `src`. Twilio credentials remain server-side only; the browser only receives the decoded audio bytes.

```
voicemail.recording_url
  └─► fetchVoicemailAudio(id)   ← apiFetch with Authorization: Bearer <token>
        └─► GET /api/voicemails/{id}/audio  (backend, auth-protected)
              └─► httpx GET Twilio recording URL  (Basic Auth, server-side only)
                    └─► audio bytes returned to frontend
  ← URL.createObjectURL(blob)
  ← <audio src="blob:..."> ← plays in browser
```

Error states:
- **Loading** → "Loading audio…" text shown
- **503 / Twilio not ready** → warning banner with the backend's exact message + **Retry** button
- **401 / 502 / any other error** → warning banner with message + **Retry** button
- **No recording_url at all** → "Recording audio not available yet." (unchanged)

### Backend — safe logging

`fetch_recording_audio()` now logs a `WARNING` for each Twilio HTTP error code (401, 403, 404, ≥400) including the voicemail ID and the status code. The Twilio `auth_token` is never logged (it is passed only via `httpx` `auth=` parameter, not interpolated into any string).

---

## Tests Run

### Backend (pytest)
```
16 passed in 3.31s  — app/tests/test_twilio_api.py
```
New tests added:
- `test_recording_callback_appends_mp3_extension_to_url`
- `test_recording_callback_does_not_double_append_mp3`
- `test_voicemail_audio_proxy_returns_correct_content_type`
- `test_voicemail_audio_proxy_returns_404_when_no_recording_url`

### Frontend (vitest)
```
50 passed (50) — 24 test files
```
New tests added:
- `renders voicemail records and quick actions` — updated for blob URL flow
- `shows retry button when audio fails to load` — new test for error + retry UI

### Frontend build (tsc + vite)
```
✓ 144 modules transformed — built in 2.38s — no TypeScript errors
```

---

## Deploy Order

1. **Backend** — no schema changes, no migration needed. Render will redeploy automatically on push.
2. **Frontend** — static build, Render will redeploy automatically on push.

Both services can deploy independently; there are no breaking API contract changes.

---

## Manual Production Verification Steps

1. Open `https://desk.techrestoredesk.com` and log in.
2. Navigate to **Settings → Voicemail Inbox**.
3. Confirm the existing voicemail (received 5/29/2026 12:16:39 PM, Unknown caller, 0:21) shows "Loading audio…" briefly, then an `<audio>` player with controls.
4. Click **Play** — verify audio plays and the status badge changes to "Listened".
5. If the recording is still 503 from Twilio (unlikely after hours), confirm the warning message and **Retry** button appear. Click Retry and try again.
6. Call `+18772683048` and leave a short test voicemail. Wait 30–60 seconds, refresh the Voicemail Inbox. Confirm the new entry appears with a working audio player.
7. Confirm that no Twilio `auth_token` value appears in browser network logs (the audio request goes to `/api/voicemails/{id}/audio`, not directly to `api.twilio.com`).
