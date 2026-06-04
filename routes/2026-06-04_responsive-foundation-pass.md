# 2026-06-04 - Responsive foundation pass

## Goal
Improve responsiveness across the app for phone and tablet breakpoints while preserving desktop usability.

## Changes made
- Added global responsive CSS breakpoints and safe media defaults.
- Made shared theme sizing tokens fluid with `clamp(...)` for buttons, inputs, panel spacing, and page title sizing.
- Updated shell behavior for tablet and mobile:
  - better breakpoint handling for sidebar collapse
  - improved top bar wrapping behavior
  - reduced visual crowding on compact widths
- Updated voicemail inbox row layout to a compact metadata arrangement on narrow screens.
- Fixed pricing header search control to avoid forcing narrow-screen horizontal squeeze.
- Improved page header action container wrapping behavior for compact layouts.

## Files touched
- frontend/src/styles/global.css
- frontend/src/styles/theme.ts
- frontend/src/components/AppShell.tsx
- frontend/src/components/PageChrome.tsx
- frontend/src/pages/VoicemailPage.tsx
- frontend/src/pages/PricingPage.tsx

## Validation
- Frontend build completed successfully (`npm run build`).
