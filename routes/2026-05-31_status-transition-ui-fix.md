# 2026-05-31 Status Transition UI Fix

## What changed

- Added workflow-aware status action derivation so Dashboard and Ticket Detail only show reachable next actions.
- Added compact primary actions with vertical-ellipsis overflow for less common valid transitions.
- Updated operator-facing status update error messages for common guardrail failures.
- Standardized Dashboard Recent Customers phone formatting through shared formatter.

## Files touched

- frontend/src/lib/repairFlow.ts
- frontend/src/pages/DashboardPage.tsx
- frontend/src/pages/TicketDetailPage.tsx
- frontend/src/pages/DashboardPage.test.tsx
- frontend/src/pages/TicketDetailPage.test.tsx
- STATUS_TRANSITION_UI_FIX_REPORT.md

## Validation

- Frontend tests passed.
- Frontend build passed.

## Notes

- Backend transition enforcement was already correct and remains unchanged.
- UI now aligns with backend transition graph to prevent rejected user actions.
