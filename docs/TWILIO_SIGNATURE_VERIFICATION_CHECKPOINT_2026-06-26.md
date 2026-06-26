# Twilio Signature Verification Checkpoint (2026-06-26)

## Scope completed

- Added centralized Twilio webhook signature verification dependency using Twilio RequestValidator.
- Enforced signature validation before business logic on Twilio-facing public webhook routes.
- Enforced production/staging rejection for signature-bypass mode.
- Added targeted negative tests for missing/forged/wrong-url/modified-body signatures and side-effect prevention.

## Protected endpoints

- POST /api/twilio/voice
- POST /api/twilio/voice/menu
- GET|POST /api/twilio/live-accept
- POST /api/twilio/recording
- GET|POST /api/twilio/outbound-call
- POST /api/market-updates/sms

## Validation behavior

- Signature is validated against configured public webhook base URL when available.
- Missing or invalid signatures return HTTP 403.
- In production/staging, TECH_RESTORE_TWILIO_SIGNATURE_BYPASS is blocked with HTTP 403.
- Development/test bypass is explicit via TECH_RESTORE_TWILIO_SIGNATURE_BYPASS=1.

## Current endpoint inventory note

No separate Twilio call-status, message-delivery-status, or customer-message callback endpoints are present in this codebase at this checkpoint. If such endpoints are introduced later, they must use the same centralized verification dependency.

## Verification summary

- Stage 2 targeted Twilio/auth signature tests: pass.
- Full backend test suite: pass.
- Full frontend test suite: pass.
- Frontend build: pass.
- Startup smoke under valid production-like config: pass.
- Production bypass rejection check: pass.
