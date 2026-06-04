# Responsive foundation pass (2026-06-04)

## Summary
This pass improves responsiveness across the app at shared layers so page-level layouts adapt better on phone/tablet without breaking desktop.

## What changed

### 1) Global responsive behavior
- Added mobile/tablet breakpoints in global stylesheet.
- Added media-safe defaults for visual elements (`img`, `svg`, `canvas`, `video`) to avoid overflow.
- Tuned heading and table density on small screens.

### 2) Shared token fluidity
Updated shared UI tokens to use fluid sizing so controls and spacing scale with viewport width:
- panel radius/padding
- primary/secondary/mini button padding
- input padding
- page title size
- page/grid spacing and min column widths

### 3) App shell adaptation
- Increased mobile-collapse breakpoint for sidebar behavior.
- Improved topbar wrapping on compact widths.
- Reduced compact-width crowding for account menu trigger and content spacing.
- Mobile sidebar now uses viewport-based width cap.

### 4) High-impact page fixups
- Voicemail inbox rows now switch to a compact metadata layout on narrower screens.
- Pricing page search input no longer forces rigid width in the page header action area.
- Page header action wrapper now shrinks/wraps more reliably.

## Validation
- `npm run build` passed.

## Next suggested step
- Add one visual e2e/mobile screenshot test sweep for key routes (Dashboard, Tickets, Voicemail, Settings) at 390px and 768px widths.
