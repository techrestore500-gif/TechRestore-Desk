# 2026-06-02 - Remove Hours Page Feature

## Goal

Remove the in-app Hours page/feature from the frontend because time tracking is moving to an external system.

## Delivered

- Removed Hours from frontend navigation and route surface
- Removed all direct Hours links from Dashboard, Tickets, and Shop Tools
- Removed Hours frontend implementation files (`HoursPage`, test, and `api/hours` client)
- Kept backend hours endpoints/tables intact to avoid risky backend surgery
- Remapped keyboard shortcut `Alt+4` to Shop Tools (`/operations`)

## Validation

- Frontend build: pass (`npm run build`)
- Backend tests: not required for this change set (frontend-only)

## Notes

- Existing customer/ticket data and all non-hours workflows remain unchanged
- Login/auth, Twilio, settings, inventory, and ticket flows are not modified by this change
