# Quick Intake Repair Workflow Redesign (2026-05-25)

## Scope

Refactor the repair intake/tracking workflow to match high-speed phone shop operations.

## Files Changed

- frontend/src/pages/IntakePage.tsx
- frontend/src/pages/DashboardPage.tsx
- frontend/src/pages/TicketDetailPage.tsx
- frontend/src/components/AppShell.tsx
- frontend/src/api/tickets.ts
- frontend/src/lib/repairFlow.ts
- frontend/src/pages/IntakePage.test.tsx
- frontend/src/pages/DashboardPage.test.tsx
- frontend/src/pages/TicketDetailPage.test.tsx
- docs/IMPLEMENTATION_STATUS.md
- docs/IMPLEMENTATION_NOTES.md

## Workflow Bottlenecks Found

- Multi-step intake wizard slowed walk-ins.
- Status updates required too many interactions and lacked scan-friendly controls.
- Main ticket workflow was table-heavy and hard to scan quickly.
- Detail page mixed high-frequency tasks with lower-frequency admin/pricing complexity.

## New Workflow

### Quick New Repair

- Single-screen intake form with only core operational fields.
- Customer typeahead and autofill via existing customer API.
- Recent device suggestions from recent repair ticket history.
- Keyboard-first UX with `Tab` navigation and `Ctrl+Enter` submit.

### Status System

- Visible status chips mapped to shop-friendly statuses:
  - New Intake
  - Diagnosing
  - Waiting for Part
  - In Repair
  - Ready for Pickup
  - Completed
  - Cannot Repair
- Backend-safe transition pathing automatically advances through required intermediate statuses.

### Repair Detail

- Workflow-first sections:
  - customer info
  - payment info
  - append-only notes log
  - parts used
  - timeline / status history
  - timestamps

### Dashboard

- Service Desk board with:
  - active repairs
  - completed today
  - waiting for parts
  - unpaid repairs
  - recent customers
- Includes search, status filtering, newest/oldest sorting, and quick status actions.

## Notes

- Payment status entered at intake is stored in the intake note payload line (`Payment status: ...`) because payment-status persistence is not yet a dedicated backend field.
- Existing backend status guardrails are preserved.
