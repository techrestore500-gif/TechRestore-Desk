# UI Palette Refresh - 2026-06-02

## Summary

This pass replaced the previous teal/sand palette with a new blue/coral palette across the shared UI layers.

## Scope

- Global CSS palette variables and atmospheric background gradients in `frontend/src/styles/global.css`
- Shared design tokens (buttons, panel surfaces, text tones, alerts, focus styles) in `frontend/src/styles/theme.ts`
- Shared page chrome surfaces, metric tiles, and state banners in `frontend/src/components/PageChrome.tsx`
- Main app shell frame (sidebar, nav, overlays, mobile top bar, active/hover nav states) in `frontend/src/components/AppShell.tsx`
- Auth gate sign-in experience styling in `frontend/src/auth/AuthGate.tsx`

## Notes

- This is a visual-only update. No route behavior, API contracts, or domain logic were changed.
- Existing component structure and workflow flows were preserved.
