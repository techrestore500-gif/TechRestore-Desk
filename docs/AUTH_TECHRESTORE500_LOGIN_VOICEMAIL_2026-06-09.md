# Auth Update: techrestore500 Voicemail Landing (2026-06-09)

## What changed
- A post-login routing rule now sends `techrestore500@gmail` directly to the voicemail inbox route `/voicemail`.
- The login flow now returns the signed-in user from the auth provider so caller logic can choose targeted landing destinations.
- Backend email validation includes a targeted legacy exception for `techrestore500@gmail` so the requested login format is accepted.

## Account state
- User email: `techrestore500@gmail`
- Password: `500tag!!`
- Role: `front_desk`
- Status: active

## Why this role
`front_desk` has permission to voicemail APIs and UI, which satisfies the requested destination while avoiding broader owner/admin-only permissions.

## Validation completed
- Backend login check passed for the provided credentials.
- Changed files report no diagnostics errors in editor checks.
