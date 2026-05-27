# 2026-05-26 Twilio Voicemail Integration

Captured the local-first Twilio voicemail feature work. The app now stores Twilio settings in SQLite with backend-only token handling, responds to inbound voice calls with TwiML, persists voicemail recordings through the recording callback, and exposes a voicemail inbox for playback, notes, status updates, and repair-ticket handoff.

The implementation stayed aligned with the existing shop workflow: voicemail is treated as another intake path, not a separate communications product. The frontend only renders inbox state and playback controls, while the backend owns all credential handling and webhook processing.
