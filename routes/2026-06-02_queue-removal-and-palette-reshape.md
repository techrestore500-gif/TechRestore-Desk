# 2026-06-02 - Queue Removal And Palette Reshape

## Goal

Remove the dedicated Queue page and its related frontend wiring, then replace the current app colors with a different overall palette.

## Delivered

- Removed the dedicated Queue page component, its test, and its data hook
- Removed Queue from sidebar navigation, page actions, dashboard shortcuts, operations quick links, keyboard shortcuts, and queue-only persisted UI store state
- Redirected `/queue` to `/tickets` so old links do not hard-fail
- Reworked the shared app palette from blue/coral to a warmer neutral terracotta/olive direction
- Updated shared visual layers in global CSS, theme tokens, app shell, page chrome, and auth gate

## Validation

- Frontend build: pass
- Frontend queue reference sweep: no remaining Queue page wiring in `src/`

## Notes

- This is a frontend-only cleanup and style change
- Backend queue APIs were not touched in this pass