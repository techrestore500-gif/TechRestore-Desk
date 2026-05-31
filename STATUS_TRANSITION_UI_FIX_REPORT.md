# Status Transition UI Fix Report

Date: 2026-05-31
Repository: tech-restore-desk
Scope: Frontend transition action safety and dashboard customer phone formatting

## Problem Summary

Dashboard and Ticket Detail surfaces were offering status actions that were not valid from the ticket's current backend status.
This caused avoidable backend rejections and poor operator experience.

## Root Cause

Frontend action rendering was based on broad, static UI status lists rather than backend-allowed transition paths.
When an operator selected an unreachable target, backend validation correctly rejected the request.

## Fixes Implemented

1. Added workflow-aware action ranking helper:
- File: frontend/src/lib/repairFlow.ts
- New helper: `getWorkflowAwareUiActions(currentStatus, transitions)`
- Behavior: returns only reachable UI status actions, sorted by shortest transition path.

2. Dashboard status actions now respect backend workflow rules:
- File: frontend/src/pages/DashboardPage.tsx
- Only valid next actions are shown.
- Primary next actions are displayed directly on card.
- Less common valid actions are moved into a vertical ellipsis overflow menu.
- Current-state and unreachable actions are not offered.
- Error messaging updated to friendly operator messages for guardrail failures.

3. Ticket Detail one-click status now respects backend workflow rules:
- File: frontend/src/pages/TicketDetailPage.tsx
- Primary next actions are shown first.
- Additional valid actions are available under a vertical ellipsis menu.
- Unreachable actions are not shown.
- Status update errors use clearer operator guidance.

4. Dashboard Recent Customers phone formatting standardized:
- File: frontend/src/pages/DashboardPage.tsx
- Uses shared formatter `formatPhone` from frontend/src/lib/format.ts.

## Test Coverage Added/Updated

1. Dashboard tests:
- File: frontend/src/pages/DashboardPage.test.tsx
- Added assertions that unreachable actions are not shown in ticket action area.
- Added assertions for standardized phone formatting.
- Added transition-path execution assertions for valid action moves.

2. Ticket Detail tests:
- File: frontend/src/pages/TicketDetailPage.test.tsx
- Added assertion that only valid next status actions are shown.

## Validation Run

Frontend tests:
- Command: `npm test -- --run`
- Result: PASS (24 files, 53 tests)

Frontend build:
- Command: `npm run build`
- Result: PASS

Backend tests:
- Not required for this fix set because backend code was not changed.

## Outcome

The frontend no longer offers status actions that backend transition rules reject.
Operators see only workflow-valid next actions, with cleaner primary actions and overflow handling for less common paths.
